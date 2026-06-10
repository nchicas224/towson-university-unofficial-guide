"""Stage 3 — Chunking.

Boundary-aware splitting (see planning.md → Chunking Strategy):
  - atomic   : one chunk per Reddit comment / review, kept whole
  - longform : paragraph-merge up to TARGET, recursively sub-split oversized
               paragraphs with OVERLAP so a fact isn't severed
  - list     : merge record lines up to TARGET

Every chunk carries metadata: source, type, subtopic, entity, chunk_index.
TARGET stays under all-MiniLM-L6-v2's 256-token ceiling (~800 chars ≈ 200 tok).
"""

from src import cleaning
from src.loaders import load_raw
from src.sources import manifest

TARGET = 800     # characters
OVERLAP = 100    # characters (long-form sub-splits only)
MIN_CHARS = 30   # drop low-signal fragments (one-word comments, page numbers)


# --- low-level splitters ------------------------------------------------------

def _split_long(text: str, size: int = TARGET, overlap: int = OVERLAP):
    """Split an oversized string into <=size pieces, breaking at a sentence or
    word boundary, carrying `overlap` chars between pieces."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            window = text[start:end]
            cut = window.rfind(". ")
            if cut < size * 0.5:
                cut = window.rfind(" ")
            end = start + cut + 1 if cut > 0 else end
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_atomic(text: str):
    """Units are blank-line separated; each becomes a chunk (sub-split if big)."""
    out = []
    for unit in text.split("\n\n"):
        unit = unit.strip()
        if unit:
            out.extend(_split_long(unit))
    return out


def chunk_longform(text: str):
    """Merge paragraphs up to TARGET; recursively split any paragraph over it."""
    chunks, buf = [], ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if len(para) > TARGET:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_split_long(para))
        elif len(buf) + len(para) + 1 <= TARGET:
            buf = f"{buf}\n{para}".strip() if buf else para
        else:
            chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    return chunks


def chunk_list(lines):
    """Greedily pack record lines into <=TARGET chunks."""
    chunks, buf = [], ""
    for ln in lines:
        if len(buf) + len(ln) + 1 <= TARGET:
            buf = f"{buf}\n{ln}".strip() if buf else ln
        else:
            if buf:
                chunks.append(buf)
            buf = ln
    if buf:
        chunks.append(buf)
    return chunks


def chunk_roomsurf(text: str):
    """Returns (chunk_text, dorm) pairs; dorm comes from '### <dorm>' headers."""
    out, dorm = [], None
    for block in (b.strip() for b in text.split("\n\n")):
        if not block:
            continue
        if block.startswith("### "):
            dorm = block[4:].strip()
            continue
        for piece in _split_long(block):
            out.append((piece, dorm))
    return out


# --- pipeline -----------------------------------------------------------------

def build_chunks():
    """Run load -> clean -> chunk for every source; return list of chunk dicts."""
    all_chunks = []
    for src in manifest():
        raw = load_raw(src)
        shape, ext = src["shape"], src["path"].suffix.lower()
        items = []  # list of (text, entity)

        if shape == "reddit":
            items = [(c, None) for c in chunk_atomic(cleaning.clean_reddit(raw))]
        elif shape == "roomsurf":
            items = chunk_roomsurf(cleaning.clean_roomsurf(raw))
        elif shape == "niche":
            stats, reviews = cleaning.clean_niche(raw)
            items = [(c, None) for c in chunk_longform(stats)]
            for review in reviews:
                items += [(c, None) for c in chunk_atomic(review)]
        elif shape == "list":
            items = [(c, None) for c in chunk_list(cleaning.clean_list(raw))]
        elif ext == ".html":
            items = [(c, None) for c in chunk_longform(cleaning.clean_html(raw))]
        elif ext == ".pdf":
            items = [(c, None) for c in chunk_longform(cleaning.clean_pdf(raw))]
        else:  # longform article .txt
            items = [(c, None) for c in chunk_longform(cleaning.clean_longform_txt(raw))]

        # drop low-signal fragments (one-word comments, stray page numbers)
        items = [(t, e) for (t, e) in items if len(t.strip()) >= MIN_CHARS]

        for i, (text, entity) in enumerate(items):
            all_chunks.append({
                "text": text,
                "source": src["filename"],
                "type": src["type"],
                "subtopic": src["subtopic"],
                "entity": entity,
                "chunk_index": i,
            })
    return all_chunks