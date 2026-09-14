"""Offline API tests (no Trino required)."""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Force mock mode before app import side effects.
os.environ["USE_MOCK_DATA"] = "1"
os.environ["API_KEY"] = ""
_fd, _auth_db = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_auth_db}"
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("APPROVED_TESTER_EMAILS", "approved.tester@example.com")
# Keep waitlist tests explicit; private mode is on by default in app code.
os.environ["PRIVATE_ACCESS_MODE"] = "0"

from app.cache import cache
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.main import app
from app.models import EmailToken, SessionToken, User


@pytest.fixture(autouse=True)
def _reset():
    get_settings.cache_clear()
    os.environ["USE_MOCK_DATA"] = "1"
    os.environ["API_KEY"] = ""
    get_settings.cache_clear()
    cache.clear()
    init_db()
    # Keep auth DB clean between tests
    db = SessionLocal()
    try:
        db.query(SessionToken).delete()
        db.query(EmailToken).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    client.cookies.clear()
    yield
    cache.clear()
    get_settings.cache_clear()


client = TestClient(app)


def _signup(email: str, password: str = "password123", **extra):
    payload = {
        "email": email,
        "password": password,
        "first_name": "T",
        "last_name": "U",
        "phone_country_code": "+234",
        "phone_number": "8012345678",
        "country_of_residence": "NG",
        **extra,
    }
    return client.post("/auth/signup", json=payload)


def _approve(user_id: str):
    return client.post(
        f"/admin/users/{user_id}/approve",
        headers={"X-Admin-Key": os.environ["ADMIN_API_KEY"]},
    )


def _approved_client(email: str = "learner@example.com"):
    res = _signup(email)
    assert res.status_code == 200
    user = res.json()["user"]
    if not user["can_run_queries"]:
        ok = _approve(user["id"])
        assert ok.status_code == 200
    return client


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["product"] == "Analytic Sages Data Portal"
    assert "Learn Blockchain Through Data" in body["tagline"]


def test_health_mock():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["mode"] == "mock"
    assert res.json()["status"] == "ok"


def test_health_tables():
    res = client.get("/health/tables")
    assert res.status_code == 200
    tables = res.json()
    assert "token_activity" in tables
    assert tables["token_activity"].endswith("token_activity")


def test_datasets_catalog():
    res = client.get("/datasets")
    assert res.status_code == 200
    body = res.json()
    assert len(body["datasets"]) >= 4
    slugs = {d["slug"] for d in body["datasets"]}
    assert {"transfers", "token_activity", "wallet_activity", "transactions"} <= slugs
    assert "bigquery_console_url" not in body
    assert "learning sandbox" in body["description"].lower() or "portal" in body["description"].lower()


def test_dataset_detail():
    res = client.get("/datasets/transfers")
    assert res.status_code == 200
    body = res.json()
    assert body["grain"].startswith("One row")
    assert body["columns"]
    assert body["sql_examples"]
    assert body["curated_table"] == "solana_curated.transfers"
    assert "FROM solana_curated.transfers" in body["sql_examples"][0]["sql"]


def test_lab_01():
    res = client.get("/labs/lab-01-explore-transfers")
    assert res.status_code == 200
    body = res.json()
    assert body["number"] == 1
    assert "FROM solana_curated.transfers" in body["starter_sql"]
    assert body["curated_table"] == "solana_curated.transfers"



def test_labs_list():
    res = client.get("/labs")
    assert res.status_code == 200
    labs = res.json()["labs"]
    assert len(labs) >= 3
    assert any(lab["slug"] == "lab-02-active-tokens" for lab in labs)


def test_lab_02():
    res = client.get("/labs/lab-02-active-tokens")
    assert res.status_code == 200
    body = res.json()
    assert body["number"] == 2
    assert "token_activity" in body["starter_sql"]
    assert body["skills"]


def test_dataset_missing():
    res = client.get("/datasets/does-not-exist")
    assert res.status_code == 404


def test_tokens_daily():
    res = client.get("/tokens/daily", params={"limit": 5})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "mock"
    assert len(body["data"]) <= 5
    assert {"block_date", "mint", "transfer_count"} <= set(body["data"][0])


def test_tokens_top():
    res = client.get("/tokens/top", params={"limit": 2})
    assert res.status_code == 200
    assert len(res.json()["data"]) <= 2


def test_token_metadata():
    mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    res = client.get(f"/tokens/{mint}")
    assert res.status_code == 200
    assert res.json()["data"]["symbol"] == "USDC"


def test_invalid_mint():
    res = client.get("/tokens/daily", params={"mint": "not-a-mint"})
    assert res.status_code == 422


def test_wallet_activity():
    address = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
    res = client.get(f"/wallets/{address}/activity", params={"limit": 3})
    assert res.status_code == 200
    assert res.json()["data"]


def test_transfers_recent():
    res = client.get("/transfers/recent", params={"limit": 5})
    assert res.status_code == 200
    assert len(res.json()["data"]) <= 5


def test_api_key_required_when_set(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    get_settings.cache_clear()
    # Recreate client after settings change; dependency reads settings at call time
    res = client.get("/datasets", headers={"X-API-Key": "wrong"})
    assert res.status_code == 401
    res = client.get("/datasets", headers={"X-API-Key": "secret"})
    assert res.status_code == 200
    monkeypatch.delenv("API_KEY", raising=False)
    get_settings.cache_clear()


def test_query_policy():
    res = client.get("/query/policy")
    assert res.status_code == 200
    body = res.json()
    assert body["max_days"] == 2
    assert body["max_bytes_billed"] > 0
    assert "solana_curated.transfers" in body["allowed_refs"]


def test_query_run_requires_auth():
    sql = (
        "SELECT mint, source AS sender, destination AS receiver, amount_ui AS amount "
        "FROM solana_curated.transfers "
        "WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) "
        "AND CURRENT_DATE() ORDER BY amount_ui DESC LIMIT 10"
    )
    res = client.post("/query/run", json={"sql": sql})
    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "EARLY_ACCESS_REQUIRED"


def test_query_run_mock():
    sql = (
        "SELECT mint, source AS sender, destination AS receiver, amount_ui AS amount "
        "FROM solana_curated.transfers "
        "WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) "
        "AND CURRENT_DATE() ORDER BY amount_ui DESC LIMIT 10"
    )
    _approved_client("runner@example.com")
    res = client.post("/query/run", json={"sql": sql})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "mock"
    assert body["row_count"] > 0


def test_query_rejects_dml():
    _approved_client("dml@example.com")
    res = client.post(
        "/query/run",
        json={"sql": "DELETE FROM solana_curated.transfers WHERE TRUE"},
    )
    assert res.status_code == 400


def test_query_rejects_old_date():
    _approved_client("olddate@example.com")
    res = client.post(
        "/query/run",
        json={
            "sql": (
                "SELECT * FROM solana_curated.transfers "
                "WHERE DATE(block_timestamp) = '2020-01-01'"
            )
        },
    )
    assert res.status_code == 400


def test_signup_waitlist_and_approve():
    res = _signup("wait@example.com")
    assert res.status_code == 200
    user = res.json()["user"]
    assert user["access_status"] == "WAITLIST_PENDING"
    assert user["can_run_queries"] is False
    me = client.get("/auth/me")
    assert me.json()["user"]["email"] == "wait@example.com"

    # Simulate email verification without leaving waitlist
    db = SessionLocal()
    try:
        row = db.query(User).filter(User.email == "wait@example.com").one()
        row.email_verified = True
        db.commit()
    finally:
        db.close()

    blocked = client.post(
        "/query/run",
        json={"sql": "SELECT 1 FROM solana_curated.transfers LIMIT 1"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["code"] == "WAITLIST_PENDING"
    _approve(user["id"])
    allowed = client.post(
        "/query/run",
        json={
            "sql": (
                "SELECT mint FROM solana_curated.transfers "
                "WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) "
                "AND CURRENT_DATE() LIMIT 5"
            )
        },
    )
    assert allowed.status_code == 200


def test_approved_tester_email_seed():
    res = _signup("approved.tester@example.com")
    assert res.status_code == 200
    user = res.json()["user"]
    assert user["is_tester"] is True
    assert user["can_run_queries"] is True
    assert user["access_status"] == "APPROVED"


def test_private_access_mode_skips_waitlist(monkeypatch):
    monkeypatch.setenv("PRIVATE_ACCESS_MODE", "1")
    res = _signup("private.user@example.com")
    assert res.status_code == 200
    user = res.json()["user"]
    assert user["access_status"] == "APPROVED"
    assert user["email_verified"] is True
    assert user["can_run_queries"] is True
    assert user["phone_country_code"] == "+234"
    assert user["country_of_residence"] == "NG"
    allowed = client.post(
        "/query/run",
        json={
            "sql": (
                "SELECT mint FROM solana_curated.transfers "
                "WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) "
                "AND CURRENT_DATE() LIMIT 5"
            )
        },
    )
    assert allowed.status_code == 200
    cfg = client.get("/auth/config")
    assert cfg.status_code == 200
    assert cfg.json()["private_access_mode"] is True
    assert cfg.json()["waitlist_enabled"] is False
    analytics = client.get(
        "/admin/analytics/summary",
        headers={"X-Admin-Key": os.environ["ADMIN_API_KEY"]},
    )
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["users"]["total"] >= 1
    assert body["queries"]["total"] >= 1


def test_admin_policy_update(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    monkeypatch.setenv("QUERY_POLICY_PATH", str(tmp_path / "policy.json"))
    res = client.put(
        "/admin/query-policy",
        headers={"X-Admin-Key": "admin-secret"},
        json={"max_days": 2, "max_rows": 50, "timeout_seconds": 20},
    )
    assert res.status_code == 200
    assert res.json()["policy"]["max_rows"] == 50
    bad = client.put(
        "/admin/query-policy",
        headers={"X-Admin-Key": "wrong"},
        json={"max_rows": 10},
    )
    assert bad.status_code == 401


def test_dashboards_catalog_defaults():
    res = client.get("/dashboards")
    assert res.status_code == 200
    body = res.json()
    assert body["counts"]["total"] >= 4
    assert body["counts"]["live"] == 0
    slugs = {d["slug"] for d in body["dashboards"]}
    assert "solana-network-activity" in slugs
    assert "solana-token-intelligence" in slugs
    assert body["journey"]["steps"]
    assert all(d["status"] == "coming_soon" for d in body["dashboards"])


def test_dashboard_detail():
    res = client.get("/dashboards/solana-token-intelligence")
    assert res.status_code == 200
    body = res.json()
    assert body["dashboard"]["slug"] == "solana-token-intelligence"
    assert "transfers" in body["dashboard"]["dataset_slugs"]


def test_dashboards_filter_by_dataset():
    res = client.get("/dashboards", params={"dataset": "transfers"})
    assert res.status_code == 200
    assert res.json()["dashboards"]
    assert all("transfers" in d["dataset_slugs"] for d in res.json()["dashboards"])


def test_learning_journey():
    res = client.get("/learning-journey")
    assert res.status_code == 200
    paths = [s["path"] for s in res.json()["steps"]]
    assert paths == ["/catalog", "/labs", "/query", "/dashboards"]


def test_studio_visualization_and_dashboard(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_STORE_PATH", str(tmp_path / "studio.json"))
    viz = client.post(
        "/studio/visualizations",
        json={
            "title": "Daily volume",
            "sql": "SELECT day, volume FROM solana_curated.transfers",
            "chart_type": "line",
            "x_axis": "day",
            "y_axis": "volume",
            "style": {"primary": "#E11D48", "palette": ["#E11D48", "#F97316"]},
        },
    )
    assert viz.status_code == 200
    assert viz.json()["visualization"]["style"]["primary"] == "#E11D48"
    viz_id = viz.json()["visualization"]["id"]
    board = client.post(
        "/studio/dashboards",
        json={"title": "My Solana board", "visualization_ids": [viz_id]},
    )
    assert board.status_code == 200
    slug = board.json()["dashboard"]["slug"]
    assert board.json()["dashboard"]["layout"]
    detail = client.get(f"/studio/dashboards/{slug}")
    assert detail.status_code == 200
    assert len(detail.json()["visualizations"]) == 1

    layout = [
        {"i": viz_id, "x": 0, "y": 0, "w": 8, "h": 10, "minW": 3, "minH": 4},
    ]
    updated = client.put(f"/studio/dashboards/{slug}", json={"layout": layout})
    assert updated.status_code == 200
    assert updated.json()["dashboard"]["layout"][0]["w"] == 8

    renamed = client.put(
        f"/studio/dashboards/{slug}",
        json={
            "title": "Weekly Solana transfers",
            "description": "Lab 3 board: daily volume and top wallets.",
        },
    )
    assert renamed.status_code == 200
    assert renamed.json()["dashboard"]["title"] == "Weekly Solana transfers"
    assert "Lab 3" in renamed.json()["dashboard"]["description"]

    share = client.post(f"/studio/dashboards/{slug}/share", json={"enabled": True})
    assert share.status_code == 200
    token = share.json()["dashboard"]["share_token"]
    assert token
    assert share.json()["dashboard"]["share_path"] == f"/share/{token}"

    themed = client.put(
        f"/studio/dashboards/{slug}",
        json={"theme": {"primary": "#0284C7", "background": "#F8FAFC"}},
    )
    assert themed.status_code == 200
    assert themed.json()["dashboard"]["theme"]["primary"] == "#0284C7"

    public = client.get(f"/public/dashboards/{token}")
    assert public.status_code == 200
    assert public.json()["dashboard"]["title"] == "Weekly Solana transfers"
    assert "Lab 3" in public.json()["dashboard"]["description"]
    assert public.json()["read_only"] is True
    assert public.json()["dashboard"]["theme"]["primary"] == "#0284C7"

    client.post(f"/studio/dashboards/{slug}/share", json={"enabled": False})
    assert client.get(f"/public/dashboards/{token}").status_code == 404


def test_admin_dashboards(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    monkeypatch.setenv("LOOKER_DASHBOARDS_PATH", str(tmp_path / "dashboards.json"))
    payload = {
        "dashboards": [
            {
                "id": "token-intelligence",
                "slug": "solana-token-intelligence",
                "title": "Solana Token Intelligence",
                "description": "Learning chart",
                "category": "token",
                "embed_url": "https://lookerstudio.google.com/reporting/abc-123/page/p_xyz",
                "is_published": True,
                "sort_order": 10,
                "dataset_slugs": ["transfers", "token_activity"],
                "charts_preview": ["Transfer volume", "Top tokens"],
            }
        ]
    }
    res = client.put(
        "/admin/dashboards",
        headers={"X-Admin-Key": "admin-secret"},
        json=payload,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["dashboards"][0]["embed_url"].startswith(
        "https://lookerstudio.google.com/embed/reporting/abc-123/page/p_xyz"
    )
    listed = client.get("/dashboards")
    assert listed.status_code == 200
    assert listed.json()["counts"]["live"] == 1
    detail = client.get("/dashboards/solana-token-intelligence")
    assert detail.json()["dashboard"]["status"] == "live"


def test_featured_showcase_dashboard(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_STORE_PATH", str(tmp_path / "showcase-studio.json"))
    from app.showcase import ensure_showcase

    ensure_showcase()
    res = client.get("/public/featured-dashboard")
    assert res.status_code == 200
    body = res.json()
    assert body["dashboard"]["slug"] == "solana-hourly-showcase"
    assert body["dashboard"]["title"] == "Solana Hourly Activity"
    assert len(body["visualizations"]) == 5
    assert body["featured"] is True

    volume_viz = next(v for v in body["visualizations"] if v["chart_type"] == "line")
    run = client.post(
        "/public/featured-dashboard/run",
        json={"visualization_id": volume_viz["id"]},
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["row_count"] >= 24
    assert "hour" in payload["columns"]
    assert "transfer_volume" in payload["columns"]


def test_rows_to_payload_prefers_result_schema():
    from app.bq_runner import _rows_to_payload

    class Field:
        def __init__(self, name):
            self.name = name

    class Row(dict):
        def __getitem__(self, key):
            return dict.__getitem__(self, key)

    class Result:
        schema = [Field("mint"), Field("amount")]

        def __iter__(self):
            return iter([Row(mint="abc", amount=1.5)])

    class Job:
        schema = None

    columns, data = _rows_to_payload(Result(), Job())
    assert columns == ["mint", "amount"]
    assert data == [{"mint": "abc", "amount": 1.5}]
