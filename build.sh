#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VERSION="$(node -p "require('./package.json').version")"
OUTPUT_PATH="$DIST_DIR/hui-lian-yi-reimbursement-$VERSION.zip"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

cd "$ROOT_DIR"

zip -r "$OUTPUT_PATH" . \
  -x '.git/*' \
  -x '.gitignore' \
  -x '.DS_Store' \
  -x 'config.local.yaml' \
  -x '.cache/*' \
  -x 'dist/*'

echo "Built $OUTPUT_PATH"
