#!/usr/bin/env bash
set -euo pipefail

BRANCH="site2026"
RESTORE_FROM="origin/main"   # change if your original theme is on another branch

# Links & contacts
YT="https://www.youtube.com/@venkateshsharmamusic2863"
FB="https://www.facebook.com/venkateshsharmamusic"
EMAIL="vsharmamusic12@gmail.com"
PHONE="+91 98452 90862"

# Raga spellings for text standardization
RAGA_CTN="Amrutadhawani"
RAGA_HIN="Gowrishankara"

# --- repo checks ---
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "Run this in repo root"; exit 1; }
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# --- sync local branch first ---
git fetch origin --quiet || true
git checkout -B "$BRANCH"
git pull --rebase origin "$BRANCH" || true

# --- safety tag ---
TAG="pre-min-text-$(date +%Y%m%d-%H%M%S)"
git tag -a "$TAG" -m "Before restoring theme + minimal text edits"

# --- restore THEME (no CSS/layout changes later) ---
git reset --hard "$RESTORE_FROM"

# ===========================================
# MINIMAL TEXT-ONLY CHANGES (Perl in-place)
# ===========================================

# 1) index.html — title/description + soft phrasing (only if phrases exist)
if [[ -f index.html ]]; then
  cp -p index.html index.html.bak

  perl -0777 -i -pe 's{<title>.*?</title>}{<title>Venkatesh Sharma — Carnatic &amp; Hindustani (Jugalbandhi) Vocalist</title>}is' index.html
  perl -0777 -i -pe 's{<meta\s+name="description"\s+content="[^"]*"}{<meta name="description" content="Official site of Venkatesh Sharma, a Carnatic–Hindustani jugalbandhi vocalist. Concerts, raga explorations, signature programs, and bookings."}i' index.html

  perl -0777 -i -pe 's{He has developed one new raga in Karnatic music namely .*? & another new raga in Hindustani namely .*?}{He has proposed two original ragas—'"$RAGA_CTN"' (Carnatic) and '"$RAGA_HIN"' (Hindustani)}i' index.html
  perl -0777 -i -pe 's{He is greatly influenced by Ustad Dilshad Khan of Mumbai and picked up the art of Khayal Singing}{Influenced by Ustad Dilshad Khan (Mumbai), he absorbed the aesthetics of Khayal singing}i' index.html
  perl -0777 -i -pe 's{and now he is equipped with the knowledge of both the music systems and emerged as one of the very few jugalbhandhi vocalists}{and today presents both traditions in thoughtfully curated jugalbandhi programs}i' index.html
fi

# 2) biography.html — minor clarity/consistency edits (if phrases present)
if [[ -f biography.html ]]; then
  cp -p biography.html biography.html.bak

  perl -0777 -i -pe 's{<title>.*?</title>}{<title>Biography — Venkatesh Sharma</title>}is' biography.html
  perl -0777 -i -pe 's{<meta\s+name="description"\s+content="[^"]*"}{<meta name="description" content="Biography of Venkatesh Sharma, vocalist performing both Carnatic and Hindustani traditions; training, programs, and recordings."}i' biography.html

  perl -0777 -i -pe 's{By that time he was an approved artist in Hindustani and Karnatic Music Category of Radio and Doordarshan}{He is an approved artist of All India Radio and Doordarshan in both Carnatic and Hindustani}i' biography.html
  perl -0777 -i -pe 's{He has conceived one new raga each in Karnatic and Hindustani Music\. In Karnatic the new raga .*? and in Hindustani Rag .*?}{He has proposed two original ragas—'"$RAGA_CTN"' (Carnatic) and '"$RAGA_HIN"' (Hindustani)}i' biography.html
  perl -0777 -i -pe 's{Jugalbandhi Concert career started}{His jugalbandhi concert work started}i' biography.html
  perl -0777 -i -pe 's{He has sung for a sanskrit film MUDRAARAKSHASA}{He has sung for the Sanskrit film Mudrarakshasa}i' biography.html
fi

# 3) video.html — insert a single links sentence AFTER THE FIRST </h1>, if not present
if [[ -f video.html ]]; then
  cp -p video.html video.html.bak

  perl -0777 -i -pe 's{<title>.*?</title>}{<title>Videos — Venkatesh Sharma</title>}is' video.html
  perl -0777 -i -pe 's{<meta\s+name="description"\s+content="[^"]*"}{<meta name="description" content="Program trailers, raga explorations, and concert highlights by Venkatesh Sharma."}i' video.html

  perl -0777 -i -pe '
    BEGIN {
      $yt = q('"$YT"');
      $fb = q('"$FB"');
      $email = q('"$EMAIL"');
      $phone = q('"$PHONE"');
      $snippet = qq{</h1>\n<p>Visit the official <a href="$yt" target="_blank" rel="noopener">YouTube channel</a> and <a href="$fb" target="_blank" rel="noopener">Facebook page</a> for the full library and updates. For bookings: <a href="mailto:$email">$email</a> · $phone.</p>};
    }
    if (index($_, "Visit the official YouTube channel") == -1) {
      s{</h1>}{$snippet}i;
    }
  ' video.html
fi

# Avoid Jekyll quirks
touch .nojekyll

# Commit & push
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "site2026: restore theme from main; minimal text-only updates (Perl edits)"
fi
git push -u origin "$BRANCH"

echo
echo "✅ Done. Theme restored; minimal text changes applied on $BRANCH."
echo "Wait ~60s for Pages to deploy, then hard refresh (Cmd/Ctrl+Shift+R)."
echo "Revert any time to tag: $TAG"
