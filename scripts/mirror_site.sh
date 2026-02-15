
#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
ORIGIN_BASE="https://vvsharma.in"   # source site
DEST_ROOT="."                       # write files into repo root
TMP_DIR="_mirror_tmp"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

# 1) Mirror the whole site (exhaustively): pages + images + pdf + css/js
#    --mirror = -r -N -l inf --no-remove-listing
#    --convert-links rewrites links for local viewing
#    --page-requisites grabs images, CSS, JS referenced by pages
#    -e robots=off because we have explicit permission from the owner
wget --mirror --convert-links --page-requisites --adjust-extension      --no-parent --no-host-directories -e robots=off      --directory-prefix "$TMP_DIR"      "$ORIGIN_BASE/"

# 2) Copy specific known pages (ensures we have them even if not linked prominently)
for p in index.html biography.html gallery.html video.html contact.php; do
  wget -x -nH -P "$TMP_DIR" -e robots=off "$ORIGIN_BASE/$p" || true
done

# 3) Standardize: convert contact.php -> contact.html (static)
if [ -f "$TMP_DIR/contact.php" ]; then
  mv "$TMP_DIR/contact.php" "$TMP_DIR/contact.html"
fi

# 4) Copy everything into the repo root
rsync -av --delete "$TMP_DIR/" "$DEST_ROOT/"

# 5) Link fixes: make internal absolute links relative; replace any lingering .php with .html
python3 scripts/postprocess.py || true

echo "Mirror complete. Review changes, then commit and push."
