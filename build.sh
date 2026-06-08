#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
SKILL_DIR="$DIST_DIR/skill"
PACKAGE_NAME="hui-lian-yi-reimbursement"
VERSION="$(node -p "require('./package.json').version")"
ZIP="$DIST_DIR/${PACKAGE_NAME}-${VERSION}.zip"

rm -rf "$DIST_DIR"
mkdir -p "$SKILL_DIR"

rsync -a \
  --exclude='.git' \
  --exclude='dist' \
  --exclude='.DS_Store' \
  --exclude='.gitignore' \
  --exclude='.env' \
  --exclude='build.sh' \
  --exclude='publish.sh' \
  --exclude='config.yaml' \
  --exclude='config.local.yaml' \
  --exclude='references/config.yaml' \
  --exclude='references/config.local.yaml' \
  --exclude='.cache' \
  "$ROOT_DIR/" "$SKILL_DIR/"

zip -r "$ZIP" "$SKILL_DIR"

echo "Built $SKILL_DIR"
echo "Zipped $ZIP"
