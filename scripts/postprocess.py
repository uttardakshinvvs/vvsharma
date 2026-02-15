
import os, re

# Replace absolute vvsharma.in URLs with relative links and .php -> .html
origin_hosts = ("http://vvsharma.in", "https://vvsharma.in")

for dirpath, _, files in os.walk('.'):
    for fn in files:
        if not fn.lower().endswith(('.html','.css','.js','.xml','.txt','.json','.htm')): continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p,'r',encoding='utf-8',errors='ignore') as f:
                s = f.read()
        except Exception:
            continue
        # Absolute to relative for this host
        for host in origin_hosts:
            s = s.replace(host+'/', './')
        # contact.php to contact.html
        s = s.replace('contact.php', 'contact.html')
        # Ensure internal anchors don't break
        s = re.sub(r'href="/(?!/)', 'href="./', s)
        with open(p,'w',encoding='utf-8') as f:
            f.write(s)
print('Postprocess link rewrite done.')
