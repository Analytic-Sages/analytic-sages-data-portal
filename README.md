# Analytic Sages Data Portal

Educational interface and data catalog for **Analytic Sages curated blockchain datasets**.

> Learn Blockchain Through Data.

Learners discover schemas, SQL examples, labs, and projects on purpose-built Solana tables.

## Architecture

```
Solana sources → AS data engineering (ingestion / dbt / Iceberg)
        ↓
Analytic Sages curated datasets
        ↓
Data Portal (this repo: frontend + API catalog)
        ↓
Learner query / visualize (BigQuery curated datasets + Looker Studio)
```

The lakehouse under `Data-pipeline/` is the engineering engine. The portal is the learner product.

## Repo layout

| Path | Role |
|------|------|
| `Data-pipeline/` | Engineer-only ingestion + transforms |
| `backend/` | FastAPI catalog + curated query API (Trino / mock) |
| `frontend/` | Learner portal UI |

## Quick start (local demo)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
USE_MOCK_DATA=1 uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend.

### Tests

```bash
cd backend
source .venv/bin/activate
USE_MOCK_DATA=1 pytest tests/ -v
```

## Live Trino mode

With Trino + BigLake available (see `backend/IMPLEMENTATION.md`):

```bash
export USE_MOCK_DATA=0
export TRINO_HOST=localhost
export TRINO_PORT=8081
uvicorn app.main:app --reload --port 8000
```

## Learner-facing curated tables

Phase 1 curated tables (learner SQL uses short form):

- `solana_curated.transfers`
- `solana_curated.token_activity`
- `solana_curated.wallet_activity`
- `solana_curated.transactions`

(Physical: `analytic-sages-data-portal.solana_curated.*`, separate from Iceberg `solana`.)

See `Data-pipeline/PHASE1_PUBLISH.md` for publish commands and Lab 01.
See `backend/LEARNING_QUERY.md` for in-portal SQL limits, `backend/STUDIO.md` for Query studio + dashboards.

Quick start for curated publish:

```bash
cd Data-pipeline
bash scripts/setup_publish_env.sh
source .venv-publish/bin/activate
gcloud auth application-default login
bash scripts/run_publish_sample.sh
```
