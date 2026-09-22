# Dashboards (Looker Studio embeds)

Learners browse dashboards at `/dashboards`. Reports are created in Looker Studio on curated
`solana_curated.*` tables and registered in the Analytic Sages dashboard catalog.

SQL labs and dashboards are separate:

- Labs teach querying (portal SQL sandbox)
- Dashboards teach visualization (Looker Studio on the same curated tables)
- Portal query result rows are **not** piped into Looker Studio

## Learner API

- `GET /learning-journey` – Catalog → Labs → Explore → Dashboards
- `GET /dashboards` – catalog (`?dataset=transfers` optional filter)
- `GET /dashboards/{slug}` – detail + embed when published

Default planned dashboards (visible as coming soon until embeds are published):

| Slug | Category | Tables |
|------|----------|--------|
| `solana-network-activity` | network | transactions, wallet_activity |
| `solana-token-intelligence` | token | transfers, token_activity |
| `solana-wallet-intelligence` | wallet | wallet_activity, transfers |
| `solana-protocol-activity` | protocol | transactions (later phase) |

## Admin publish

```bash
export ADMIN_API_KEY=your-secret

curl -X PUT http://localhost:8000/admin/dashboards \
  -H "X-Admin-Key: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboards": [
      {
        "id": "token-intelligence",
        "slug": "solana-token-intelligence",
        "title": "Solana Token Intelligence",
        "description": "Transfer volume, top tokens, sender/receiver patterns",
        "category": "token",
        "embed_url": "https://lookerstudio.google.com/reporting/REPORT_ID/page/PAGE_ID",
        "is_published": true,
        "sort_order": 20,
        "dataset_slugs": ["transfers", "token_activity"],
        "charts_preview": ["Transfer volume", "Top tokens", "Unique senders"]
      }
    ]
  }'
```

Report URLs are rewritten to `/embed/reporting/...` automatically. Published dashboards require
`embed_url`.

## Setup checklist

1. Looker Studio → connect BigQuery → `analytic-sages-data-portal.solana_curated.*`
2. Build charts on the report canvas (KPIs, line/bar charts, filters)
3. File → Embed report; share for viewers (often “Anyone with the link” for a learning sandbox)
4. Prefer data-source credentials so learners do not need GCP/BQ IAM
5. `PUT /admin/dashboards` with the embed URL and `is_published: true`

## Env

| Env | Purpose |
|-----|---------|
| `LOOKER_DASHBOARDS_PATH` | JSON persistence for the catalog |
| `LOOKER_STUDIO_REPORTS` | Optional `id\|title\|embed_url\|dataset;...` override |
| `ADMIN_API_KEY` | Protects admin writes |

Do **not** add the Looker Studio / Data Studio management API for MVP.
