#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$ROOT_DIR/dist/skill"
VERSION="$(grep '^version:' "$ROOT_DIR/SKILL.md" | sed 's/version: *"\(.*\)"/\1/')"

# Load local secrets if present.
[ -f "$ROOT_DIR/.env" ] && set -a && source "$ROOT_DIR/.env" && set +a

_OLD_REGISTRY="${CLAWHUB_REGISTRY:-}"
export CLAWHUB_REGISTRY="https://skillhub.distinctclinic.com/"
trap 'export CLAWHUB_REGISTRY="$_OLD_REGISTRY"' EXIT

echo "Building..."
"$ROOT_DIR/build.sh"

echo "Logging in to $CLAWHUB_REGISTRY ..."
if [ -n "${CLAWHUB_TOKEN:-}" ]; then
  npx clawhub login --token "$CLAWHUB_TOKEN" --no-browser
else
  npx clawhub login
fi

echo "Publishing $SKILL_DIR@$VERSION to $CLAWHUB_REGISTRY ..."
npx clawhub publish "$SKILL_DIR" --version "$VERSION"

echo "Done."
