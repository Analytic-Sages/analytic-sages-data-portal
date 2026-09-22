#!/usr/bin/env bash
# Create an isolated venv for curated BigQuery publish (do not use conda base).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv-publish"
REQ="$ROOT/jobs/requirements-publish.txt"

python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$REQ"

echo
echo "Publish env ready: $VENV"
echo "Next:"
echo "  source $VENV/bin/activate"
echo "  gcloud auth application-default login"
echo "  cd $ROOT/jobs"
echo "  python publish/publish_curated_bq.py --source sample --project analytic-sages-data-portal"
