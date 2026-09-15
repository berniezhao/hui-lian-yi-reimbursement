#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
SKILL_DIR="$DIST_DIR/skill"
PACKAGE_NAME="hui-lian-yi-reimbursement"

# Validate before touching dist. Resolve inputs from the script, never caller cwd.
node - "$ROOT_DIR" <<'NODE'
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const text = fs.readFileSync(path.join(root, 'SKILL.md'), 'utf8');
const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
const versions = frontmatter ? [...frontmatter[1].matchAll(/^version:\s*(?:"([^"\r\n]+)"|'([^'\r\n]+)'|([^\s#]+))\s*$/gm)] : [];
const version = versions.length === 1 ? (versions[0][1] || versions[0][2] || versions[0][3]) : null;
const semver = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/;
if (!version || !semver.test(version) || typeof pkg.version !== 'string' || !semver.test(pkg.version) || version !== pkg.version) {
  console.error('Build refused: SKILL.md must have one valid SemVer version matching package.json.');
  process.exit(1);
}
NODE
VERSION="$(node -p 'require(process.argv[1]).version' "$ROOT_DIR/package.json")"
ZIP="$DIST_DIR/${PACKAGE_NAME}-${VERSION}.zip"

rm -rf "$DIST_DIR"
mkdir -p "$SKILL_DIR"

# Explicit distributable inputs avoid copying private runtime or developer files.
for item in SKILL.md config.example.yaml package.json README.md references agents scripts assets; do
  if [[ -e "$ROOT_DIR/$item" ]]; then
    rsync -a \
      --exclude='.git' --exclude='.claude' --exclude='.cache' \
      --exclude='dist' --exclude='.DS_Store' --exclude='.env*' \
      --exclude='config.yaml' --exclude='config.local.yaml' \
      "$ROOT_DIR/$item" "$SKILL_DIR/"
  fi
done

# Archive paths are relative and portable; never embed absolute local paths.
(cd "$DIST_DIR" && zip -qr "$ZIP" skill)
echo "Built $SKILL_DIR"
echo "Zipped $ZIP"
