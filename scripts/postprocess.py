import os, re

origin_hosts = ("http://vvsharma.in", "https://vvsharma.in")

def fix_text(s: str) -> str:
    for host in origin_hosts:
        s = s.replace(host + "/", "./").replace(host, ".")
    # PHP → HTML
    s = s.replace("contact.php", "contact.html")
    # root-absolute → relative in HTML
    s = re.sub(r'(?i)(href|src)\s*=\s*"/', r'\1="./', s)
    return s

def fix_css(s: str) -> str:
    s = s.replace("https://vvsharma.in/", "./").replace("http://vvsharma.in/", "./")
    # url(/img/...) → url(./img/...)
    s = re.sub(r'url\(\s*[\'"]?/(?!/)', 'url(./', s, flags=re.IGNORECASE)
    return s

for dirpath, _, files in os.walk("."):
    for fn in files:
        low = fn.lower()
        if not low.endswith((".html", ".css", ".js", ".xml", ".txt", ".json", ".htm")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                s = f.read()
        except Exception:
            continue
        ns = fix_css(s) if low.endswith(".css") else fix_text(s)
        if ns != s:
            with open(p, "w", encoding="utf-8") as f:
                f.write(ns)

print("Postprocess: HTML & CSS links rewritten to relative, contact.php → contact.html")
