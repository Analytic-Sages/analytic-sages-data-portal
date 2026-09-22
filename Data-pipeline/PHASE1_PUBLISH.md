# Phase 1: Curated BigQuery publish

## Goal

A learner can query Analytic Sages curated Solana tables in BigQuery.

## Important

Learner curated tables live in **`solana_curated`**, not the lake/Iceberg dataset `solana`.

| Lake (engineers) | Curated (learners) |
|------------------|--------------------|
| `...solana.transfers` (Iceberg) | `...solana_curated.token_transfers` (native BQ) |

## Learner SQL style

With project `analytic-sages-data-portal` selected in BigQuery:

```sql
FROM solana_curated.token_transfers
```

Full path (ops only): `analytic-sages-data-portal.solana_curated.token_transfers`

## Tables

| Learner reference | Grain |
|-------------------|-------|
| `solana_curated.token_transfers` | One row per token transfer |
| `solana_curated.transactions` | One row per transaction |
| `solana_curated.token_activity` | One row per token per day |
| `solana_curated.wallet_activity` | One row per wallet per day |

## Setup (one time)

```bash
cd Data-pipeline
bash scripts/setup_publish_env.sh
source .venv-publish/bin/activate
gcloud auth application-default login
gcloud config set project analytic-sages-data-portal
```

## Publish sample data

From `Data-pipeline` (do not `cd Data-pipeline` again if you are already there):

```bash
source .venv-publish/bin/activate
bash scripts/run_publish_sample.sh
```

## Prove end-to-end

1. Publish prints `Publish complete` for the four `solana_curated` tables
2. Restart portal API if needed
3. Portal → Labs → **Lab 01** → **Run in portal** (results table should show columns and values)
4. Portal → **Dashboards** after an admin publishes Looker Studio embeds (`backend/LOOKER_STUDIO.md`)

In-portal querying: `backend/LEARNING_QUERY.md` (bytes billed, timeout, max rows, 2-day window, admin `PUT /admin/query-policy`).

## Portal env

```bash
export BQ_PROJECT=analytic-sages-data-portal
export BQ_CURATED_DATASET=solana_curated
export USE_MOCK_DATA=0
export QUERY_MAX_DAYS=2
export QUERY_MAX_BYTES_BILLED=104857600
export QUERY_TIMEOUT_SECONDS=30
export QUERY_MAX_ROWS=100
export ADMIN_API_KEY=your-secret
```
