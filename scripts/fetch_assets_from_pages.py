#!/usr/bin/env python3
import os, re, sys, time, urllib.parse, pathlib, html as htmlmod, ssl
from urllib.request import Request, urlopen

ORIGIN = "https://vvsharma.in"
PAGES = [
    "index.html",       # Home
    "biography.html",   # Biography
    "gallery.html",     # Gallery
    "video.html",       # Videos
    "contact.php",      # Contact (will become contact.html)
]
UA  = "Mozilla/5.0 (compatible; SitePreserver/1.0; +https://github.com/uttardakshinvvs/vvsharma)"
CTX = ssl.create_default_context()

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urlopen(req, context=CTX, timeout=30) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def norm_same_host(url: str) -> str | None:
    """Return a normalized same-host https URL or None if external/data."""
    if not url or url.startswith(("data:", "mailto:", "tel:")):
        return None
    parsed = urllib.parse.urlparse(url)
    # If relative, prefix origin
    if not parsed.scheme:
        url = urllib.parse.urljoin(ORIGIN + "/", url)
        parsed = urllib.parse.urlparse(url)
    # Keep only same-host
    if parsed.netloc and parsed.netloc not in ("vvsharma.in",):
        return None
    # Normalize scheme/host
    norm = parsed._replace(scheme="https", netloc="vvsharma.in", params="", query="", fragment="")
    return urllib.parse.urlunparse(norm)

def page_out_name(src: str) -> str:
    # Save contact.php as contact.html for Pages
    return "contact.html" if src.endswith("contact.php") else os.path.basename(src)

def local_path_for(origin_url: str) -> str:
    parsed = urllib.parse.urlparse(origin_url)
    path = parsed.path.lstrip("/")
    if path == "contact.php":
        path = "contact.html"
    return "./" + path

def collect_html_asset_urls(html_bytes: bytes, page_url: str) -> set[str]:
    s = html_bytes.decode("utf-8", errors="ignore")
    urls: set[str] = set()
    # <img src="">
    for m in re.finditer(r'(?i)<img[^>]+src\s*=\s*"([^"]+)"', s):
        u = norm_same_host(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
        if u: urls.add(u)
    # <link href="">
    for m in re.finditer(r'(?i)<link[^>]+href\s*=\s*"([^"]+)"', s):
        u = norm_same_host(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
        if u: urls.add(u)
    # <script src="">
    for m in re.finditer(r'(?i)<script[^>]+src\s*=\s*"([^"]+)"', s):
        u = norm_same_host(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
        if u: urls.add(u)
    # Anchors to PDFs/images
    for m in re.finditer(r'(?i)<a[^>]+href\s*=\s*"([^"]+\.(?:pdf|jpe?g|png|gif|webp|svg|woff2?|ttf|otf))"', s):
        u = norm_same_host(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
        if u: urls.add(u)
    return urls

def collect_css_urls(css_bytes: bytes, css_base_url: str) -> set[str]:
    s = css_bytes.decode("utf-8", errors="ignore")
    urls: set[str] = set()
    # url(...) patterns, including quoted/unquoted forms
    for m in re.finditer(r'url\\(\\s*[\'"]?([^\'")?#]+)', s, re.IGNORECASE):
        raw = m.group(1).strip()
        # Resolve relative to the CSS file location
        absu = urllib.parse.urljoin(css_base_url, raw)
        u = norm_same_host(absu)
        if u:
            # Filter only likely asset types (images/fonts)
            if re.search(r'\\.(?:jpe?g|png|gif|webp|svg|ico|woff2?|ttf|otf)$', u, re.I):
                urls.add(u)
    return urls

def rewrite_html_links(html_bytes: bytes) -> bytes:
    s = html_bytes.decode("utf-8", errors="ignore")
    s = s.replace("https://vvsharma.in/", "./").replace("http://vvsharma.in/", "./")
    # root-absolute → relative
    s = re.sub(r'(?i)(href|src)\\s*=\\s*"/', r'\\1="./', s)
    # PHP → HTML
    s = s.replace("contact.php", "contact.html")
    return s.encode("utf-8")

def rewrite_css_urls(css_bytes: bytes) -> bytes:
    s = css_bytes.decode("utf-8", errors="ignore")
    s = s.replace("https://vvsharma.in/", "./").replace("http://vvsharma.in/", "./")
    # url(/img/hero.jpg) → url(./img/hero.jpg)
    s = re.sub(r'url\\(\\s*[\'"]?/(?!/)', 'url(./', s)
    return s.encode("utf-8")

def main():
    all_assets: set[str] = set()
    css_files: list[tuple[str, str]] = []  # (local_path, origin_url)

    # 1) Fetch & normalize key pages; collect HTML-level assets
    for page in PAGES:
        page_url = urllib.parse.urljoin(ORIGIN + "/", page)
        try:
            html_bytes = fetch(page_url)
        except Exception as e:
            print(f"[warn] failed to fetch {page}: {e}", file=sys.stderr)
            continue

        out_name = page_out_name(page)
        fixed = rewrite_html_links(html_bytes)
        ensure_dir(out_name)
        with open(out_name, "wb") as f:
            f.write(fixed)

        assets = collect_html_asset_urls(html_bytes, page_url)
        all_assets |= assets

    # 2) Download assets gathered from HTML (CSS, JS, images, PDFs)
    for a in sorted(all_assets):
        lp = local_path_for(a)
        try:
            b = fetch(a)
        except Exception as e:
            print(f"[warn] asset fetch failed {a}: {e}", file=sys.stderr)
            continue

        ensure_dir(lp)
        with open(lp, "wb") as f:
            f.write(b)

        # Track CSS so we can parse for url(...) dependencies
        if lp.lower().endswith(".css"):
            css_files.append((lp, a))

    # 3) Parse downloaded CSS files to find url(...) assets; fetch those too
    css_assets: set[str] = set()
    for local_css, origin_css in css_files:
        try:
            css_bytes = open(local_css, "rb").read()
        except Exception:
            continue
        # Rewrite CSS URLs inline to relative
        with open(local_css, "wb") as f:
            f.write(rewrite_css_urls(css_bytes))

        # Then extract assets and fetch each
        found = collect_css_urls(css_bytes, origin_css)
        css_assets |= found

    for a in sorted(css_assets):
        lp = local_path_for(a)
        try:
            b = fetch(a)
        except Exception as e:
            print(f"[warn] css asset fetch failed {a}: {e}", file=sys.stderr)
            continue
        ensure_dir(lp)
        with open(lp, "wb") as f:
            f.write(b)

    print(f"Fetched {len(all_assets)} HTML assets and {len(css_assets)} CSS-linked assets.")

if __name__ == "__main__":
    main()
