#!/usr/bin/env python3
import os, re, sys, time, urllib.parse, pathlib
import html
import ssl
from urllib.request import Request, urlopen

ORIGIN = "https://vvsharma.in"
PAGES = [
    "index.html",       # Home
    "biography.html",   # Biography
    "gallery.html",     # Gallery
    "video.html",       # Videos
    "contact.php",      # Contact (will become contact.html)
]

UA = "Mozilla/5.0 (compatible; SitePreserver/1.0; +https://github.com/uttardakshinvvs/vvsharma)"
CTX = ssl.create_default_context()

def fetch(url):
    req = Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urlopen(req, context=CTX, timeout=30) as r:
                return r.read()
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))

def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def norm_asset_url(page_url, raw):
    raw = html.unescape(raw.strip())
    if raw.startswith("data:") or raw.startswith("mailto:") or raw.startswith("tel:"):
        return None
    u = urllib.parse.urljoin(page_url, raw)
    # keep only same-host resources
    parsed = urllib.parse.urlparse(u)
    if parsed.netloc and parsed.netloc not in ("vvsharma.in",):
        # external resource -> keep external (e.g., YouTube); we won't download
        return None
    return urllib.parse.urlunparse(("https", "vvsharma.in", parsed.path, "", "", ""))

def local_path_from_origin(origin_url):
    # map https://vvsharma.in/img/foo.jpg -> ./img/foo.jpg
    parsed = urllib.parse.urlparse(origin_url)
    path = parsed.path.lstrip("/")
    # normalize .php to .html for contact page if needed
    if path == "contact.php": path = "contact.html"
    return "./" + path

def collect_urls(html_bytes, page_url):
    s = html_bytes.decode("utf-8", errors="ignore")
    urls = set()
    # img src
    for m in re.finditer(r'(?i)<img[^>]+src\s*=\s*"([^"]+)"', s):
        u = norm_asset_url(page_url, m.group(1))
        if u: urls.add(u)
    # link href (css/pdf/ico)
    for m in re.finditer(r'(?i)<link[^>]+href\s*=\s*"([^"]+)"', s):
        u = norm_asset_url(page_url, m.group(1))
        if u: urls.add(u)
    # script src
    for m in re.finditer(r'(?i)<script[^>]+src\s*=\s*"([^"]+)"', s):
        u = norm_asset_url(page_url, m.group(1))
        if u: urls.add(u)
    # anchor PDFs and images
    for m in re.finditer(r'(?i)<a[^>]+href\s*=\s*"([^"]+\.(?:pdf|jpg|jpeg|png|gif|webp|svg))"', s):
        u = norm_asset_url(page_url, m.group(1))
        if u: urls.add(u)
    return urls

def rewrite_links_to_relative(html_bytes):
    s = html_bytes.decode("utf-8", errors="ignore")
    # host-absolute -> relative
    s = s.replace("https://vvsharma.in/", "./").replace("http://vvsharma.in/", "./")
    # root-absolute -> relative (href="/img/..." -> "./img/...")
    s = re.sub(r'(?i)(href|src)\s*=\s*"/', r'\1="./', s)
    # PHP -> HTML for contact page
    s = s.replace("contact.php", "contact.html")
    return s.encode("utf-8")

def main():
    # fetch and save each page; collect assets
    assets = set()
    for p in PAGES:
        page_url = urllib.parse.urljoin(ORIGIN + "/", p)
        try:
            html_bytes = fetch(page_url)
        except Exception as e:
            # allow failure of a single page; continue
            print(f"[warn] failed to fetch {p}: {e}", file=sys.stderr)
            continue
        out_name = p if p != "contact.php" else "contact.html"
        fixed = rewrite_links_to_relative(html_bytes)
        ensure_dir(out_name)
        with open(out_name, "wb") as f:
            f.write(fixed)
        assets |= collect_urls(html_bytes, page_url)

    # download assets individually (no directory listing)
    for a in sorted(assets):
        lp = local_path_from_origin(a)
        try:
            content = fetch(a)
        except Exception as e:
            print(f"[warn] asset fetch failed {a}: {e}", file=sys.stderr)
            continue
        ensure_dir(lp)
        with open(lp, "wb") as f:
            f.write(content)

    print(f"Fetched {len(assets)} asset(s) referenced by key pages.")

if __name__ == "__main__":
    main()
