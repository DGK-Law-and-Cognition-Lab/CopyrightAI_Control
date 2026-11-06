#!/bin/bash
# Copy a study's accepted images into its stimuli/ folder (for B1, replacing
# the grey placeholders and removing the placeholder marker so the deploy
# script will push).
#   tools/install_images.sh B1     Set B: Stimuli/Paper Two/setB/web/ (SB-P1_V1.jpg, SB-P1_I2.jpg, ...)
#   tools/install_images.sh A1     Set A: Stimuli/Paper Two/setA/web/ (SA01_source.jpg, SA01_small.jpg, ...)
# A1 uses ten scenes, with the reserves in the places of the scenes they
# replaced (SA-R1 for SA05, SA-R2 for SA08), each as source, small, medium
# and large: 40 files. Every copy is compared byte for byte with its source.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
STUDY="${1:?Usage: tools/install_images.sh <study, e.g. B1 or A1>}"
DEST="$HERE/$STUDY/stimuli"
case "$STUDY" in
  B1)
    SRC="$HERE/../setB/web"
    SCENES="SB-P1 SB-N1 SB-P2 SB-N2 SB-P3 SB-R2 SB-P4 SB-N4 SB-P5 SB-N5 SB-P6 SB-N6"
    KINDS="V1 I2"
    ;;
  A1)
    SRC="$HERE/../setA/web"
    SCENES="SA01 SA06 SA02 SA07 SA03 SA-R2 SA04 SA09 SA-R1 SA10"
    KINDS="source small medium large"
    ;;
  *) echo "No image list for study $STUDY. Nothing changed."; exit 1 ;;
esac
[ -d "$SRC" ] || { echo "No folder $SRC yet. Nothing changed."; exit 1; }
mkdir -p "$DEST"
n=0; missing=0
for s in $SCENES; do for c in $KINDS; do
  n=$((n + 1))
  [ -f "$SRC/${s}_${c}.jpg" ] || { echo "Missing $SRC/${s}_${c}.jpg"; missing=1; }
done; done
[ "$missing" = 0 ] || { echo "Not all $n files exist yet. Nothing changed."; exit 1; }
for s in $SCENES; do for c in $KINDS; do
  f="${s}_${c}.jpg"
  cp "$SRC/$f" "$DEST/$f"
  cmp -s "$SRC/$f" "$DEST/$f" || { echo "STOP: $f did not copy exactly."; exit 1; }
  kb=$(( $(stat -f%z "$DEST/$f") / 1024 ))
  [ "$kb" -le 800 ] || echo "Note: $f is ${kb} KB; consider compressing it (about 300 KB loads quickly)."
done; done
rm -f "$DEST/PLACEHOLDER_IMAGES.txt"
echo "Installed $n images into $STUDY/stimuli/ (each identical to $SRC) and removed any placeholder marker."
