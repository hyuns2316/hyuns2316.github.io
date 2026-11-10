#!/usr/bin/env python3
"""Attach newly uploaded images to publications that still use the placeholder thumbnail.

Run by .github/workflows/thumb-sync.yml when images are added under assets/img/.
Usage: thumb_sync.py <new image path> [<new image path> ...]

Matching, per placeholder entry in _data/publications.yml:
  1. Filename words that start a word of the title (e.g. cor_sel.png -> "Correspondence
     Selection", vlm_3dvg.png -> "VLM-based ...") score a match; best score wins.
  2. If no name matches but exactly one entry and one image are left, they are paired.
Writes a PR summary to .thumb_sync_summary.md when anything changed.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / "_data" / "publications.yml"
SUMMARY = ROOT / ".thumb_sync_summary.md"
PLACEHOLDER = "./assets/img/teaser_example.png"
EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def words(text):
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]


def score(image, title):
    stem_words = [w for w in words(Path(image).stem) if len(w) >= 2]
    title_words = words(title)
    return sum(1 for s in stem_words if any(t.startswith(s) for t in title_words))


def main(paths):
    images = [p for p in paths if Path(p).suffix.lower() in EXTS and Path(p).name != Path(PLACEHOLDER).name]
    text = PUBS.read_text(encoding="utf-8")
    # (title, start offset of its "image:" line) for every entry still on the placeholder
    entries = []
    for m in re.finditer(r'(?m)^  - title:\s*"?(.*?)"?\s*$', text):
        nxt = re.search(r"(?m)^  - title:", text[m.end():])
        end = m.end() + nxt.start() if nxt else len(text)
        img = re.search(r"(?m)^    image:\s*(.*)$", text[m.end():end])
        if img and img.group(1).strip() == PLACEHOLDER:
            entries.append((m.group(1), m.end() + img.start(1), m.end() + img.end(1)))

    pairs = []
    left_imgs, left_entries = list(images), list(entries)
    while left_imgs and left_entries:
        best = max(((score(i, e[0]), i, e) for i in left_imgs for e in left_entries), key=lambda x: x[0])
        if best[0] == 0:
            break
        pairs.append((best[1], best[2]))
        left_imgs.remove(best[1])
        left_entries.remove(best[2])
    if not pairs and len(left_imgs) == 1 and len(left_entries) == 1:
        pairs.append((left_imgs[0], left_entries[0]))
        left_imgs, left_entries = [], []

    if not pairs:
        print("No placeholder entry matched the new image(s).")
        return
    for img, (_, s, e) in sorted(pairs, key=lambda p: -p[1][1]):  # edit from the end
        text = text[:s] + "./" + img + text[e:]
    PUBS.write_text(text, encoding="utf-8")

    lines = ["Thumbnails were set from newly uploaded images:\n"]
    lines += [f"- `{img}` → {title}" for img, (title, _, _) in pairs]
    if left_imgs:
        lines += ["", "Not matched to any paper (left unused): " + ", ".join(f"`{i}`" for i in left_imgs)]
    lines += ["", "Check the pairing in **Files changed**, then merge."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
