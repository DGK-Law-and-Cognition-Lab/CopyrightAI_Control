#!/bin/bash
# Copy the shared engine (engine.js, style.css, captcha.png) from ../engine into
# a study folder, so the study folder stays deployable on its own.
#   tools/sync_engine.sh B1
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
STUDY="${1:?Usage: tools/sync_engine.sh <study folder, e.g. B1>}"
DEST="$HERE/$STUDY"
[ -d "$DEST" ] || { echo "No folder $DEST"; exit 1; }
for f in engine.js style.css captcha.png; do
  cp "$HERE/engine/$f" "$DEST/$f"
  echo "copied engine/$f -> $STUDY/$f"
done
