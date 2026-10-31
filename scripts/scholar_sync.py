#!/usr/bin/env python3
"""Detect new Google Scholar papers and add draft entries to _data/publications.yml.

Run by .github/workflows/scholar-sync.yml. The workflow turns any changes into a
Pull Request, so nothing reaches the live site until the owner merges it.

Files:
  _data/publications.yml   site's publication list (new drafts are inserted at the top)
  _data/scholar_seen.yml   Scholar titles already handled; a title listed here is never proposed again

First run: if scholar_seen.yml does not exist, every paper currently on Scholar is
recorded as "seen" and nothing is added, so only papers published afterwards are proposed.
"""
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

SCHOLAR_USER = os.environ.get("SCHOLAR_USER", "kjrkW3AAAAAJ")
OWNER_NAME = os.environ.get("OWNER_NAME", "Hyunsoo Shin")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / "_data" / "publications.yml"
SEEN = ROOT / "_data" / "scholar_seen.yml"
SUMMARY = ROOT / ".scholar_sync_summary.md"  # read by the workflow for the PR body

BASE = "https://scholar.google.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def norm(title: str) -> str:
    t = unicodedata.normalize("NFKD", title or "").lower()
    return re.sub(r"[^a-z0-9]+", "", t)


# ---------------------------------------------------------------- fetching

def get(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200 or "gs_captcha" in r.text or "unusual traffic" in r.text:
        raise RuntimeError(f"Google Scholar blocked the request (HTTP {r.status_code}).")
    return r.text


def fetch_direct():
    """Scrape the public profile page. Returns list of dicts."""
    papers, start = [], 0
    while True:
        html = get(f"{BASE}/citations", {
            "user": SCHOLAR_USER, "hl": "en", "cstart": start,
            "pagesize": 100, "sortby": "pubdate",
        })
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tr.gsc_a_tr")
        for row in rows:
            a = row.select_one("a.gsc_a_at")
            if not a:
                continue
            grays = row.select("div.gs_gray")
            venue = ""
            if len(grays) > 1:
                for s in grays[1].select("span.gs_oph"):
                    s.decompose()
                venue = grays[1].get_text(" ", strip=True)
            year = row.select_one("span.gsc_a_h")
            papers.append({
                "title": a.get_text(strip=True),
                "authors": grays[0].get_text(strip=True) if grays else "",
                "venue": venue,
                "year": year.get_text(strip=True) if year else "",
                "detail": BASE + a.get("href", "") if a.get("href") else "",
                "link": "",
            })
        if len(rows) < 100:
            break
        start += 100
        time.sleep(3)
    return papers


def enrich_direct(p):
    """Open the paper's Scholar detail page for full authors, venue and publisher link."""
    if not p["detail"]:
        return
    time.sleep(3)
    soup = BeautifulSoup(get(p["detail"]), "html.parser")
    link = soup.select_one("a.gsc_oci_title_link")
    if link and link.get("href"):
        p["link"] = link["href"]
    fields = {}
    for row in soup.select("div.gs_scl"):
        k, v = row.select_one(".gsc_oci_field"), row.select_one(".gsc_oci_value")
        if k and v:
            fields[k.get_text(strip=True).lower()] = v.get_text(" ", strip=True)
    if fields.get("authors"):
        p["authors"] = fields["authors"]
    for key in ("journal", "conference", "book", "source"):
        if fields.get(key):
            p["venue"] = fields[key]
            break
    m = re.search(r"\d{4}", fields.get("publication date", ""))
    if m:
        p["year"] = m.group(0)


def fetch_serpapi():
    papers, start = [], 0
    while True:
        r = requests.get("https://serpapi.com/search.json", params={
            "engine": "google_scholar_author", "author_id": SCHOLAR_USER,
            "hl": "en", "sort": "pubdate", "num": 100, "start": start,
            "api_key": SERPAPI_KEY,
        }, timeout=60)
        r.raise_for_status()
        arts = r.json().get("articles", [])
        for a in arts:
            venue = re.sub(r",\s*\d{4}\s*$", "", a.get("publication", "") or "")
            papers.append({
                "title": a.get("title", ""), "authors": a.get("authors", ""),
                "venue": venue, "year": str(a.get("year", "") or ""),
                "detail": a.get("link", ""), "link": "",
            })
        if len(arts) < 100:
            break
        start += 100
    return papers


# ---------------------------------------------------------------- yaml

def q(s: str) -> str:
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def bold_owner(authors: str) -> str:
    """Bold the owner's name (handles 'Hyunsoo Shin' and Scholar's 'H Shin')."""
    first, last = OWNER_NAME.split()[0], OWNER_NAME.split()[-1]
    pat = re.compile(rf"\b({re.escape(OWNER_NAME)}|{first[0]}\.?\s*{re.escape(last)})\b")
    return pat.sub(lambda m: f"<strong>{m.group(1)}</strong>", authors, count=1)


def entry_text(p) -> str:
    venue = ", ".join(x for x in (p["venue"], p["year"]) if x)
    return (
        f"  # TODO(scholar-sync): check authors, set conference_short / image / bibtex\n"
        f"  - title: {q(p['title'])}\n"
        f"    authors: {q(bold_owner(p['authors']))}\n"
        f"    conference_short: \"TODO\"\n"
        f"    conference: {q(venue + '.' if venue else '')}\n"
        f"    pdf: {p['link'] or p['detail']}\n"
        f"    bibtex:\n"
        f"    image: ./assets/img/teaser_example.png\n"
        f"    notes:\n\n"
    )


def main():
    try:
        papers = fetch_serpapi() if SERPAPI_KEY else fetch_direct()
    except Exception as e:  # blocked or network error: fail loudly, change nothing
        print(f"::error::{e}")
        sys.exit(1)
    if not papers:
        print("::error::No papers parsed from Scholar (page layout may have changed).")
        sys.exit(1)
    print(f"Scholar returned {len(papers)} papers.")

    site_titles = {norm(x.get("title", "")) for x in
                   (yaml.safe_load(PUBS.read_text(encoding="utf-8")) or {}).get("main", [])}

    if not SEEN.exists():
        titles = sorted({p["title"] for p in papers})
        SEEN.write_text(
            "# Scholar titles already handled by scholar-sync. Titles here are never proposed again.\n"
            "# Delete a line to have that paper proposed on the next run.\n"
            + yaml.safe_dump({"seen": titles}, allow_unicode=True, sort_keys=False, width=1000),
            encoding="utf-8")
        SUMMARY.write_text(
            f"First run: recorded {len(titles)} existing Scholar papers as the baseline. "
            "From now on only newly added Scholar papers will be proposed.\n", encoding="utf-8")
        print("Baseline created.")
        return

    seen = yaml.safe_load(SEEN.read_text(encoding="utf-8")) or {}
    seen_list = seen.get("seen", []) or []
    seen_norm = {norm(t) for t in seen_list}

    new = [p for p in papers if norm(p["title"]) not in seen_norm | site_titles]
    if not new:
        print("No new papers.")
        return

    for p in new:
        if not SERPAPI_KEY:
            try:
                enrich_direct(p)
            except Exception as e:
                print(f"warning: could not open detail page for {p['title']!r}: {e}")

    text = PUBS.read_text(encoding="utf-8")
    m = re.search(r"^main:\s*\n", text, re.M)
    head, rest = (text[:m.start()] + "main:\n\n", text[m.end():]) if m else ("main:\n\n", text)
    block = "".join(entry_text(p) for p in new)
    PUBS.write_text(head + block + rest.lstrip("\n"), encoding="utf-8")

    seen_text = SEEN.read_text(encoding="utf-8").rstrip("\n") + "\n"
    seen_text += "".join(f"- {q(p['title'])}\n" for p in new)
    SEEN.write_text(seen_text, encoding="utf-8")

    lines = [f"Found **{len(new)}** new paper(s) on Google Scholar:\n"]
    lines += [f"- {p['title']} ({p['venue']}, {p['year']})" for p in new]
    lines += [
        "",
        "Draft entries were added to the top of `_data/publications.yml`. Before merging:",
        "- Check the author list (Scholar sometimes abbreviates names).",
        "- Replace `conference_short: \"TODO\"` with the venue badge text.",
        "- Add a thumbnail under `assets/img/` and update `image:`; add a `.bib` file if wanted.",
        "- To skip a paper, delete its entry from `publications.yml` in this PR but keep it in "
        "`scholar_seen.yml`, then merge — it will not be proposed again.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Added {len(new)} draft entr{'y' if len(new) == 1 else 'ies'}.")


if __name__ == "__main__":
    main()
