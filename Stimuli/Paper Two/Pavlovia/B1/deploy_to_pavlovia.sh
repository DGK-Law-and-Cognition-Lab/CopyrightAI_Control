#!/bin/bash
# Push Paper B Study 1 (B1) to ONE Pavlovia project, the one you created for it.
#
# Set PROJECT below to its path (for example "dgkamper/paper-b-study-1"), or
# leave it empty and type it when asked. The script clones
# https://gitlab.pavlovia.org/<PROJECT>.git, checks the clone points there,
# replaces the page files, shows what changes, and pushes only after you type
# the project's name (the part after the slash). It never pushes config.json
# (Pavlovia serves its own) and never touches the data/ folder.
#
# Files pushed: index.html config.js engine.js style.css captcha.png
#               open_rows.json stimuli/*.jpg
# It stops if engine.js, style.css or captcha.png differ from ../engine
# (run ../tools/sync_engine.sh B1), or if the placeholder images are still in
# stimuli/ (run ../tools/install_images.sh B1).
# Git asks for your Pavlovia GitLab username and password or token.

set -euo pipefail

PROJECT=""

SRC="$(cd "$(dirname "$0")" && pwd)"
ENGINE="$SRC/../engine"
FILES=(index.html config.js engine.js style.css captcha.png open_rows.json)

if [ -z "$PROJECT" ] && [ -f "$SRC/.pavlovia_project" ]; then PROJECT="$(cat "$SRC/.pavlovia_project")"; fi
if [ -z "$PROJECT" ]; then
  read -r -p "Pavlovia project path for B1 (owner/name, as in gitlab.pavlovia.org/owner/name): " PROJECT
fi
[[ "$PROJECT" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo "STOP: '$PROJECT' is not owner/name."; exit 1; }
NAME="${PROJECT#*/}"
TARGET="https://gitlab.pavlovia.org/$PROJECT.git"

echo "============================================================"
echo " B1 will be pushed to: https://gitlab.pavlovia.org/$PROJECT"
echo " Run link:             https://run.pavlovia.org/$PROJECT"
echo "============================================================"

for f in "${FILES[@]}"; do [ -f "$SRC/$f" ] || { echo "Missing $SRC/$f"; exit 1; }; done
for f in engine.js style.css captcha.png; do
  cmp -s "$SRC/$f" "$ENGINE/$f" || { echo "STOP: $f differs from ../engine/$f. Run ../tools/sync_engine.sh B1 first."; exit 1; }
done
if [ -f "$SRC/stimuli/PLACEHOLDER_IMAGES.txt" ]; then
  echo "STOP: stimuli/ still holds the grey placeholder images. Run ../tools/install_images.sh B1 first."
  read -r -p "Type 'push placeholders' to push them anyway (test project only): " ph
  [ "$ph" = "push placeholders" ] || exit 1
fi
n=$(ls "$SRC"/stimuli/SB-*_V1.jpg "$SRC"/stimuli/SB-*_I2.jpg 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = "24" ] || { echo "STOP: expected 24 images in stimuli/, found $n."; exit 1; }
if grep -q "var SONA_CREDIT_URL_BASE = '';" "$SRC/config.js"; then
  echo "WARNING: SONA_CREDIT_URL_BASE in config.js is empty, so SONA participants will not be"
  echo "         credited automatically. Set it before the SONA listing opens."
fi

WORK="$(mktemp -d)"
echo "Cloning into $WORK ..."
git clone --quiet "$TARGET" "$WORK/repo"
cd "$WORK/repo"
ORIGIN="$(git remote get-url origin)"
[ "$ORIGIN" = "$TARGET" ] || { echo "STOP: the clone points to $ORIGIN, not $TARGET. Nothing was pushed."; exit 1; }
if git rev-parse --verify --quiet HEAD > /dev/null; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
else
  echo "Note: the repository is empty (a new project). The first push creates branch master."
  BRANCH="master"
  git checkout --quiet -b master
fi
if [ -d data ] && [ -n "$(ls -A data 2>/dev/null)" ]; then
  echo "Note: data/ already holds $(ls data | wc -l | tr -d ' ') files; they are left untouched."
fi

mkdir -p stimuli
for f in "${FILES[@]}"; do cp "$SRC/$f" "./$f"; done
cp "$SRC"/stimuli/SB-*_V1.jpg "$SRC"/stimuli/SB-*_I2.jpg stimuli/
git add "${FILES[@]}" stimuli
if git diff --cached --quiet; then echo "Nothing changed; nothing to push."; exit 0; fi
echo
echo "Files that will be added or changed in $PROJECT:"
git diff --cached --stat
echo
read -r -p "Type $NAME to push, or anything else to stop: " ok
[ "$ok" = "$NAME" ] || { echo "Not pushed. Clone left at $WORK"; exit 0; }
git commit --quiet -m "B1: page files and stimuli"
git push --quiet origin "HEAD:refs/heads/$BRANCH"
echo "$PROJECT" > "$SRC/.pavlovia_project"
echo
echo "Pushed to $PROJECT (branch $BRANCH)."
echo "Your own test run (no SONA, no credit):"
echo "  https://run.pavlovia.org/$PROJECT/index.html?participant=PILOT_DK1"
echo "Automatic test run (fills every answer):"
echo "  https://run.pavlovia.org/$PROJECT/index.html?test=1&code=12345"
