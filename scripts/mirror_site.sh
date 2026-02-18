#!/usr/bin/env bash
set -euo pipefail

ORIGIN_BASE="https://vvsharma.com"
TMP_DIR="_mirror_tmp"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

UA="Mozilla/5.0 (compatible; SitePreserver/1.0; +https://github.com/uttardakshinvvs/vvsharma)"

mirror_cmd () {
  local ipflag="$1" # "-4" or "" (default)
  wget $ipflag \
    --user-agent="$UA" \
    --mirror --convert-links --page-requisites --adjust-extension \
    --no-parent --no-host-directories -e robots=off \
    --timeout=30 --tries=3 --waitretry=5 --retry-connrefused \
    --content-on-error --no-check-certificate \
    --directory-prefix "$TMP_DIR" \
    "$ORIGIN_BASE/"
}

# Retry up to 4 cycles with backoff; try IPv4 first
ok=0
for attempt in 1 2 3 4; do
  echo "Mirror attempt #$attempt (IPv4)..."
  if mirror_cmd "-4"; then ok=1; break; fi
  echo "Mirror attempt #$attempt (default stack)..."
  if mirror_cmd ""; then ok=1; break; fi
  sleep $((attempt * 10))
done

# Pull critical pages explicitly, even if the full mirror struggled
for p in index.html biography.html gallery.html video.html contact.php; do
  wget -x -nH -P "$TMP_DIR" -e robots=off \
    --user-agent="$UA" --timeout=30 --tries=3 --waitretry=5 --no-check-certificate \
    "$ORIGIN_BASE/$p" || true
done

# Convert the PHP contact form to static HTML so it works on GitHub Pages
if [ -f "$TMP_DIR/contact.php" ]; then
  mv "$TMP_DIR/contact.php" "$TMP_DIR/contact.html"
fi

# Copy everything into repo root
rsync -av "$TMP_DIR/" "./" || true

# If nothing was fetched, return non-zero to trigger fallbacks in the workflow
if [ ! -f "./index.html" ]; then
  echo "Primary mirror did not retrieve index.html"
  exit 8
fi

echo "Primary mirror completed."
