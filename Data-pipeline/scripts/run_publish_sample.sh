#!/usr/bin/env bash
# Run sample curated publish using the isolated publish venv.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv-publish"
PROJECT="${BQ_PROJECT:-analytic-sages-data-portal}"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Publish venv missing. Run: bash $ROOT/scripts/setup_publish_env.sh"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
cd "$ROOT/jobs"
exec python publish/publish_curated_bq.py --source sample --project "$PROJECT" "$@"
