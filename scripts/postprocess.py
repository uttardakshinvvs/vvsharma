import os, re

ORIGINS = ("http://vvsharma.com", "https://vvsharma.com")

def fix_html(s: str) -> str:
    for host in ORIGINS:
        s = s.replace(host + "/", "./").replace(host, ".")
    s = s.replace("contact.php", "contact.html")
    s = re.sub(r'(?i)(href|src)\s*=\s*"/', r'\1="./', s)
    return s

for dirpath, _, files in os.walk("."):
    for fn in files:
        low = fn.lower()
        if not low.endswith((".html",".js",".xml",".txt",".json",".htm",".css")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            s = open(p, "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        ns = fix_html(s) if not low.endswith(".css") else s
        if ns != s:
            open(p, "w", encoding="utf-8").write(ns)

print("Postprocess done (HTML host/root fixes; CSS handled in parser).")
