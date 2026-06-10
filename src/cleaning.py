"""Stage 2 — Cleaning.

Turns each loaded source into clean, normalized text with natural-unit
boundaries marked by blank lines (``\\n\\n``). Chunking (Stage 3) then reads
those boundaries — keeping atomic units whole, merging long-form paragraphs.

What we remove (per the Milestone 3 spec): HTML tags, nav menus, footers,
social links, repeated contact blocks, share/CTA widgets, emoji decorations,
and review-card metadata (dates, ids, reviewer initials). What we keep: the
actual prose, opinions, ratings, prices, and policy text.

Roomsurf reviews keep a ``### <dorm>`` header before each block so chunking can
record which dorm a review is about (the ``entity`` metadata field).
"""

import html
import re

# --- shared normalization ----------------------------------------------------

_SMART = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ", "•": "-",
}


def normalize_text(s: str) -> str:
    """Decode HTML entities, fold smart punctuation to ASCII, collapse spaces."""
    s = html.unescape(html.unescape(s))   # twice: Reddit double-encodes (&amp;#x200B;)
    for bad, good in _SMART.items():
        s = s.replace(bad, good)
    s = s.replace("​", "").replace("﻿", "").replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def _lines(s: str):
    return [ln.strip() for ln in s.splitlines()]


# --- HTML (longform) ----------------------------------------------------------

from bs4 import BeautifulSoup  # noqa: E402

_HTML_DROP_TAGS = ["script", "style", "nav", "header", "footer", "form",
                   "button", "svg", "noscript"]
# Short label/nav lines that survive inside <main> on towson.edu pages.
_HTML_DROP_LINES = {
    "sub-menu", "contact", "location", "hours", "phone", "fax", "email",
    "facebook", "twitter", "youtube", "instagram", "monday - friday",
}


def clean_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    main = soup.find("main") or soup.body or soup
    for tag in main(_HTML_DROP_TAGS):
        tag.decompose()

    blocks, seen = [], set()
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        txt = normalize_text(el.get_text(" ", strip=True))
        if not txt or txt.lower() in _HTML_DROP_LINES:
            continue
        if txt in seen:                  # drop repeated nav/menu duplicates
            continue
        seen.add(txt)
        blocks.append(txt)

    # The trailing repeated "Department of Housing & Residence Life" contact
    # block appears on every page — truncate from there if present.
    for i, b in enumerate(blocks):
        if b.startswith("Department of Housing") or b.startswith("Dean of Students"):
            blocks = blocks[:i]
            break
    return "\n\n".join(blocks)


# --- Reddit (.json, atomic) ---------------------------------------------------

_DEAD = {"[deleted]", "[removed]", ""}


def clean_reddit(data) -> str:
    units = []
    post = data[0]["data"]["children"][0]["data"]
    title = normalize_text(post.get("title", ""))
    body = normalize_text(post.get("selftext", ""))
    units.append((title + "\n" + body).strip() if body else title)

    def walk(children):
        for ch in children:
            if ch.get("kind") != "t1":
                continue
            b = normalize_text(ch["data"].get("body", ""))
            b = re.sub(r"(?m)^\s*>\s?", "", b).strip()   # drop markdown quote markers
            if b not in _DEAD:
                units.append(b)
            replies = ch["data"].get("replies")
            if isinstance(replies, dict):
                walk(replies["data"]["children"])

    walk(data[1]["data"]["children"])
    return "\n\n".join(u for u in units if u)


# --- Roomsurf reviews (.txt, atomic) ------------------------------------------

_ROOMSURF_HEADER = re.compile(r"^(.*?) Dorm Reviews at Towson University$")


def clean_roomsurf(raw: str) -> str:
    out, dorm = [], None
    for ln in _lines(raw):
        if not ln:
            continue
        m = _ROOMSURF_HEADER.match(ln)
        if m:
            dorm = m.group(1).strip()
            if dorm.lower().startswith("see "):   # nav: "See all ...", skip
                dorm = None
                continue
            out.append(f"### {dorm}")
            continue
        # Review bodies are long prose; everything else (emoji, dates, #ids,
        # ratings, names, "Get Started", nav) is short — drop by length.
        if len(ln) >= 50:
            out.append(normalize_text(ln))
    return "\n\n".join(out)


# --- Niche (.txt) — stats block + atomic reviews ------------------------------

_NICHE_DROP = {
    "schedule your tour", "take a virtual tour", "get recruited by colleges",
    "find college scholarships", "homes for sale", "map is loaded",
    "improve this map",
}
_NICHE_REVIEW_MARK = re.compile(r"^Rating .* out of 5\s*reviews$", re.I)


def clean_niche(raw: str):
    """Returns (stats_text, [review, ...]). Stats is paragraph-like; reviews
    are atomic units."""
    lines = [ln for ln in _lines(raw) if ln]
    split_at = next((i for i, ln in enumerate(lines)
                     if ln.lower().startswith("reviews about campus life")), len(lines))
    stats_lines = [normalize_text(ln) for ln in lines[:split_at]
                   if ln.lower() not in _NICHE_DROP and "© mapbox" not in ln.lower()]

    reviews, current = [], []
    for ln in lines[split_at:]:
        if _NICHE_REVIEW_MARK.match(ln):
            if current:
                reviews.append(" ".join(current).strip())
            current = []
        elif re.match(r"^(Freshman|Sophomore|Junior|Senior|Alum)", ln) or \
                ln.lower().endswith("found this helpful") or ln == "Report":
            continue  # reviewer/date footer
        elif len(ln) >= 40:
            current.append(normalize_text(ln))
    if current:
        reviews.append(" ".join(current).strip())
    return "\n".join(stats_lines), reviews


# --- Structured lists (.txt) --------------------------------------------------

_LIST_DROP = {
    "skip to content", "skip to chat", "logo", "sign in", "catering",
    "about us", "contact us", "careers", "events", "cookie preferences",
    "terms of use", "privacy policy", "do not sell my personal information",
    "sitemap", "© aramark 2026", "meal plans", "dining dollars",
    "locations & menus", "get directions", "summer hours hours", "show all",
    "open now", "dining halls", "restaurants", "convenience", "grab-n-go",
    "sort by distance", "all locations", "closed", "open", "get started",
}


def clean_list(raw: str):
    """Drop nav/footer/UI lines and transient hours; keep record lines."""
    out = []
    for ln in _lines(raw):
        if not ln:
            continue
        low = ln.lower()
        if low in _LIST_DROP or low.startswith("opens on") or low.startswith("© "):
            continue
        out.append(normalize_text(ln))
    return out


# --- generic long-form text (.txt article, .pdf) ------------------------------

_TXT_DROP = {
    "school", "shares", "see also", "featured image source:",
    "sign up to our newsletter", "get notified about exclusive offers every week!",
}


_PDF_DOTS = re.compile(r"\.{4,}")            # TOC dotted leaders
_PDF_HEADER = re.compile(r"^PARKING REGULATIONS (APPROVED|FALL)", re.I)


def clean_pdf(raw: str) -> str:
    """Drop repeated page headers/footers, page numbers, and TOC dot-leaders;
    rebuild one paragraph per page (pages were joined with blank lines by the
    loader). Long pages get recursively sub-split downstream."""
    from collections import Counter

    all_lines = [normalize_text(ln) for ln in raw.splitlines()]
    freq = Counter(ln for ln in all_lines if ln)
    repeated = {ln for ln, c in freq.items() if c >= 4 and len(ln) < 90}

    pages = []
    for page in raw.split("\n\n"):
        kept = []
        for ln in (normalize_text(x) for x in page.splitlines()):
            if not ln or ln in repeated:
                continue
            if _PDF_HEADER.match(ln) or re.fullmatch(r"\d+", ln) or _PDF_DOTS.search(ln):
                continue
            kept.append(ln)
        if kept:
            pages.append(" ".join(kept))
    return "\n\n".join(pages)


def clean_longform_txt(raw: str) -> str:
    """Normalize and rebuild paragraphs from blank-line breaks; drop obvious
    article boilerplate (share counts, newsletter, related-article widgets)."""
    paras, cur = [], []
    for ln in _lines(raw):
        low = ln.lower()
        if not ln:
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        if low in _TXT_DROP or ln.isdigit() or low.startswith("featured image"):
            continue
        cur.append(normalize_text(ln))
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(p for p in paras if p)