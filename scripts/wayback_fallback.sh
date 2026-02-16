#!/usr/bin/env bash
set -euo pipefail

pages=(
  "index.html"
  "biography.html"
  "gallery.html"
  "video.html"
  "contact.html"
)

base="https://web.archive.org/web/2025*/"  # any 2025 snapshot; change if needed

for p in "${pages[@]}"; do
  if [ ! -f "$p" ]; then
    echo "Wayback fallback for $p"
    # try a few timestamps (broad to narrow)
    for ts in 20251231 20250701 20250101; do
      url="${base}https://vvsharma.in/${p/index.html/}"
      # Special case: contact.html was contact.php on origin
      if [ "$p" = "contact.html" ]; then
        url="${base}https://vvsharma.in/contact.php"
      fi
      echo "  trying $url"
      if curl -fsL --max-time 20 "$url" -o "$p"; then
        echo "  archived copy saved for $p"
        break
      fi
    done
  fi
done

# Try to fetch archived PDF if not present
if [ ! -f "img/profile.pdf" ]; then
  mkdir -p img
  for ts in 20251231 20250701 20250101; do
    pdf_url="https://web.archive.org/web/${ts}/https://vvsharma.in/img/profile.pdf"
    echo "Wayback fallback for profile.pdf -> $pdf_url"
    if curl -fsL --max-time 20 "$pdf_url" -o "img/profile.pdf"; then
      echo "  archived profile.pdf saved."
      break
    fi
  done
fi
