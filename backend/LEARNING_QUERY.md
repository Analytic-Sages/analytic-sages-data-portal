# In-portal learning queries (not Dune)

Learners can run SQL inside the portal against curated BigQuery tables, with hard admin limits.

## Learner API

- `GET /query/policy` – current limits
- `POST /query/run` – `{ "sql": "SELECT ... FROM solana_curated.token_transfers ..." }`

## Default limits (env)

| Env | Default | Meaning |
|-----|---------|---------|
| `QUERY_ENABLED` | `1` | Turn sandbox on/off |
| `QUERY_MAX_BYTES_BILLED` | `104857600` (100 MB) | Hard BigQuery bytes billed cap |
| `QUERY_TIMEOUT_SECONDS` | `30` | Job timeout |
| `QUERY_MAX_ROWS` | `100` | Result row cap |
| `QUERY_MAX_DAYS` | `2` | Learning data window |
| `QUERY_ALLOWED_DATASET` | `solana_curated` | Only this dataset |
| `QUERY_ALLOWED_TABLES` | transfers,transactions,token_activity,wallet_activity | Allow-list |
| `ADMIN_API_KEY` | (required for admin) | Protects policy updates |
| `QUERY_POLICY_PATH` | `backend/var/query_policy.json` | Runtime overrides |

## Admin control

```bash
export ADMIN_API_KEY=your-secret

curl -X PUT http://localhost:8000/admin/query-policy \
  -H "X-Admin-Key: your-secret" \
  -H "Content-Type: application/json" \
  -d '{"max_days":2,"max_bytes_billed":52428800,"timeout_seconds":20,"max_rows":50}'
```

Guards:

- SELECT/WITH only
- allow-listed `solana_curated.*` tables only
- date literals must fall inside the max_days window
- dry-run byte estimate must be under max_bytes_billed
- BigQuery `maximum_bytes_billed` + timeout enforced on the job

Learners use **Run in portal** only. There is no “Open in BigQuery” CTA in the product UI.

Looker Studio dashboards: see `LOOKER_STUDIO.md`.
