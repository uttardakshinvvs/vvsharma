#!/usr/bin/env python3
import os, re, sys, time, urllib.parse, ssl, html as htmlmod
from urllib.request import Request, urlopen
from pathlib import Path

ORIGIN = "https://vvsharma.com"
PAGES = [
    "index.html",
    "biography.html",
    "gallery.html",
    "video.html",
    "contact.php",  # saved as contact.html
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
    if not url or url.startswith(("data:", "mailto:", "tel:")):
        return None
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = urllib.parse.urljoin(ORIGIN + "/", url)
        parsed = urllib.parse.urlparse(url)
    if parsed.netloc and parsed.netloc not in ("vvsharma.com",):
        return None
    norm = parsed._replace(scheme="https", netloc="vvsharma.com", params="", query="", fragment="")
    return urllib.parse.urlunparse(norm)

def page_out_name(src: str) -> str:
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
    def add(u):
        u = norm_same_host(u);  urls.add(u) if u else None

    # <img src="">
    for m in re.finditer(r'(?i)<img[^>]+src\s*=\s*"([^"]+)"', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    # <link href="">
    for m in re.finditer(r'(?i)<link[^>]+href\s*=\s*"([^"]+)"', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    # <script src="">
    for m in re.finditer(r'(?i)<script[^>]+src\s*=\s*"([^"]+)"', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    # <audio>/<source> src
    for m in re.finditer(r'(?i)<(?:audio|source)[^>]+src\s*=\s*"([^"]+)"', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    # inline url(...) in style=""
    for m in re.finditer(r'(?i)style\s*=\s*"[^"]*url\(\s*[\'"]?([^\'")?#]+)', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    # anchors to files
    for m in re.finditer(r'(?i)<a[^>]+href\s*=\s*"([^"]+\.(?:pdf|jpe?g|png|gif|webp|svg|ico|woff2?|ttf|otf|mp3|m4a|wav))"', s):
        add(urllib.parse.urljoin(page_url, htmlmod.unescape(m.group(1))))
    return urls

def find_css_urls(css_text: str, css_base_url: str) -> list[tuple[str,str]]:
    """Return [(raw_ref, origin_url)] pairs found in CSS url(...)."""
    out: list[tuple[str,str]] = []
    for m in re.finditer(r'url\(\s*[\'"]?([^\'")?#]+)', css_text, flags=re.IGNORECASE):
        raw = m.group(1).strip()
        absu = urllib.parse.urljoin(css_base_url, raw)
        u = norm_same_host(absu)
        if u and re.search(r'\.(?:jpe?g|png|gif|webp|svg|ico|woff2?|ttf|otf)$', u, re.I):
            out.append((raw, u))
    return out

def rewrite_html_links(html_bytes: bytes) -> bytes:
    s = html_bytes.decode("utf-8", errors="ignore")
    s = s.replace("https://vvsharma.com/", "./").replace("http://vvsharma.com/", "./")
    s = re.sub(r'(?i)(href|src)\s*=\s*"/', r'\1="./', s)  # root-abs → rel
    s = s.replace("contact.php", "contact.html")
    return s.encode("utf-8")

def css_rewrite_to_rel(css_text: str, css_local_path: str, pairs: list[tuple[str, str]]) -> str:
    """
    For each (raw_ref, origin_url) in pairs:
      - compute local saved file path for origin_url
      - compute relative path from css file’s folder to that local file
      - replace url(raw_ref) (quoted/unquoted) with url(relative_path)
    """
    css_dir = Path(css_local_path).parent.resolve()
    for raw, origin in pairs:
        local = Path(local_path_for(origin)).resolve()
        try:
            rel = os.path.relpath(local, start=css_dir)
        except Exception:
            rel = local.name  # fallback: just filename
        # Replace any quoting format
        pattern = re.compile(r'url\(\s*[\'"]?'+re.escape(raw)+r'\s*[\'"]?\)', flags=re.IGNORECASE)
        css_text = pattern.sub(f"url({rel})", css_text)
    # Also convert host-absolute leftovers to relative to CSS file
    css_text = css_text.replace("https://vvsharma.com/", "")
    css_text = css_text.replace("http://vvsharma.com/", "")
    return css_text

def main():
    all_assets: set[str] = set()
    css_files: list[tuple[str, str]] = []  # (local_css_path, origin_css_url)

    # 1) Fetch pages, normalize links, collect page-level assets
    for page in PAGES:
        page_url = urllib.parse.urljoin(ORIGIN + "/", page)
        try:
            html_bytes = fetch(page_url)
        except Exception as e:
            print(f"[warn] failed to fetch {page}: {e}", file=sys.stderr)
            continue
        out_name = page_out_name(page)
        ensure_dir(out_name)
        with open(out_name, "wb") as f:
            f.write(rewrite_html_links(html_bytes))
        all_assets |= collect_html_asset_urls(html_bytes, page_url)

    # 2) Download HTML-discovered assets (CSS, JS, images, audio, pdf)
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
        if lp.lower().endswith(".css"):
            css_files.append((lp, a))

    # 3) Parse/rewrite CSS and fetch url(...) dependencies
    for local_css, origin_css in css_files:
        try:
            css_text = Path(local_css).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        pairs = find_css_urls(css_text, origin_css)
        # Download CSS-linked assets
        for _, origin in pairs:
            lp = local_path_for(origin)
            try:
                b = fetch(origin)
                ensure_dir(lp)
                with open(lp, "wb") as f:
                    f.write(b)
            except Exception as e:
                print(f"[warn] css asset fetch failed {origin}: {e}", file=sys.stderr)
                continue
        # Rewrite the CSS urls to *correct relative* paths
        new_css = css_rewrite_to_rel(css_text, local_css, pairs)
        Path(local_css).write_text(new_css, encoding="utf-8")

    print(f"Fetched {len(all_assets)} HTML assets and rewrote {len(css_files)} CSS file(s).")

if __name__ == "__main__":
    main()
