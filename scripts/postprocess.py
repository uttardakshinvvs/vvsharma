import os, re

origin_hosts = ("http://vvsharma.in", "https://vvsharma.in")

def fix_paths(s: str) -> str:
    # 1) Replace absolute host with relative
    for host in origin_hosts:
        s = s.replace(host + "/", "./")
        s = s.replace(host, ".")

    # 2) Root-absolute → relative for common attributes
    #    src="/img/..." or href="/img/..." -> "./img/..."
    s = re.sub(r'(?i)(src|href)\s*=\s*"\/(img\/[^"]+)"', r'\1="./\2"', s)

    # 3) contact.php -> contact.html (Pages is static)
    s = s.replace("contact.php", "contact.html")

    # 4) Make remaining site-root href="/..." relative
    s = re.sub(r'(?i)href\s*=\s*"\/(?!\/)', r'href="./', s)
    s = re.sub(r'(?i)src\s*=\s*"\/(?!\/)', r'src="./', s)

    return s

for dirpath, _, files in os.walk("."):
    for fn in files:
        if not fn.lower().endswith((".html",".css",".js",".xml",".txt",".json",".htm")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                s = f.read()
        except Exception:
            continue
        ns = fix_paths(s)
        if ns != s:
            with open(p, "w", encoding="utf-8") as f:
                f.write(ns)

print("Postprocess: links rewritten to relative, contact.php -> contact.html")
