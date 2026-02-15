# Venkatesh Sharma — GitHub Pages Mirror

**Generated:** 2026-02-15

This repository is structured to mirror and preserve the current site **vvsharma.in** as static pages on GitHub Pages, including **biography**, **gallery**, **videos**, **contact**, and all linked assets (images, CSS/JS, and the publicly linked **profile.pdf**).

> We have explicit permission from the artist to back up and republish the content. For reference, the public pages we target include: Home, Biography, Gallery, Videos, Contact, and the profile PDF. See: home ([index](https://vvsharma.in/index.html)), biography ([biography.html](https://vvsharma.in/biography.html)), gallery ([gallery.html](https://vvsharma.in/gallery.html)), videos ([video.html](https://vvsharma.in/video.html)), contact ([contact.php](https://vvsharma.in/contact.php)), and the profile PDF ([img/profile.pdf](https://vvsharma.in/img/profile.pdf)).

## How to use

### One-time from your computer
```bash
# prerequisites: git, bash, wget, python3, rsync
./scripts/mirror_site.sh
# review files, then:
git add -A
git commit -m "Initial mirror"
git push
```

### Or run the GitHub Action (no local setup)
- Go to **Actions → Mirror vvsharma.in to Pages repo → Run workflow**.
- The workflow uses `wget` to crawl the site recursively, rewrites links, and commits the mirrored content back to the repo.

### GitHub Pages
- In this repo: **Settings → Pages → Build & deployment → Deploy from a branch → main / root**. GitHub Pages serves `index.html` and other static files. (Docs: publishing source, entry files.)

## Notes
- `contact.php` is converted to `contact.html` (static) because GitHub Pages does not execute PHP. The contact details are preserved in the static page.
- All absolute links to `vvsharma.in` are rewritten to be relative; PDFs and images are brought into the repo so the site works even if the original domain expires.
- If any third‑party embeds (e.g., YouTube) are listed on the Videos page, they will remain external and continue to work.

## Attributions
- Source pages: [index.html](https://vvsharma.in/index.html), [biography.html](https://vvsharma.in/biography.html), [gallery.html](https://vvsharma.in/gallery.html), [video.html](https://vvsharma.in/video.html), [contact.php](https://vvsharma.in/contact.php). Public profile PDF: [img/profile.pdf](https://vvsharma.in/img/profile.pdf).

