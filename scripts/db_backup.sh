#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$OUTPUT_DIR/f1-races_$TIMESTAMP.dump"

mkdir -p "$OUTPUT_DIR"

pg_dump --dbname="$DATABASE_URL" --format=custom --file="$FILE"

echo "Backup written to $FILE"
