#!/bin/bash
# Daily during data collection: count analyzable participants per row from the
# data on Pavlovia, rewrite open_rows.json so full rows close, and push only
# open_rows.json back to the study's Pavlovia project.
#   tools/daily_update.sh B1
# Uses the project path saved by the deploy script (<study>/.pavlovia_project)
# or asks for it. If tools/prior_codes.txt exists (SONA codes of everyone who
# took part in Paper One, a Paper A or B study, or Prompt Position), those codes
# are excluded. Prints counts only; it never shows anyone's answers.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
STUDY="${1:?Usage: tools/daily_update.sh <study, e.g. B1>}"
PFILE="$HERE/$STUDY/.pavlovia_project"
if [ -f "$PFILE" ]; then PROJECT="$(cat "$PFILE")"; else read -r -p "Pavlovia project path (owner/name): " PROJECT; fi
[[ "$PROJECT" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo "STOP: '$PROJECT' is not owner/name."; exit 1; }
NAME="${PROJECT#*/}"
TARGET="https://gitlab.pavlovia.org/$PROJECT.git"
WORK="$(mktemp -d)"
git clone --quiet "$TARGET" "$WORK/repo"
[ "$(git -C "$WORK/repo" remote get-url origin)" = "$TARGET" ] || { echo "STOP: clone points elsewhere."; exit 1; }
[ -d "$WORK/repo/data" ] || { echo "No data/ folder yet in $PROJECT; nothing to count."; exit 0; }
PRIOR=()
[ -f "$HERE/tools/prior_codes.txt" ] && PRIOR=(--prior-codes "$HERE/tools/prior_codes.txt")
python3 "$HERE/tools/update_open_rows.py" --study "$STUDY" --data "$WORK/repo/data" "${PRIOR[@]+"${PRIOR[@]}"}"
cp "$HERE/$STUDY/open_rows.json" "$WORK/repo/open_rows.json"
cd "$WORK/repo"
git add open_rows.json
if git diff --cached --quiet; then echo "open_rows.json unchanged; nothing to push."; exit 0; fi
read -r -p "Type $NAME to push the new open_rows.json, or anything else to stop: " ok
[ "$ok" = "$NAME" ] || { echo "Not pushed. Clone left at $WORK"; exit 0; }
git commit --quiet -m "$STUDY: daily open_rows.json update"
git push --quiet origin "HEAD:refs/heads/$(git rev-parse --abbrev-ref HEAD)"
echo "Pushed open_rows.json to $PROJECT."
