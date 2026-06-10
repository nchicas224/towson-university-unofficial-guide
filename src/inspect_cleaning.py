"""Stage 2 test — clean a representative doc of each shape and eyeball it.

Run from the repo root:  python -m src.inspect_cleaning
"""

from src import cleaning
from src.loaders import load_raw
from src.sources import manifest

# one representative file per shape
SAMPLES = {
    "reddit": "parking_at_towson.json",
    "roomsurf": "dorm_reviews.txt",
    "niche": "niche_campus_life.txt",
    "list": "locations_and_menus.txt",
    "longform": "glen_complex.html",
}


def clean_for(src, raw):
    shape, ext = src["shape"], src["path"].suffix.lower()
    if shape == "reddit":
        return cleaning.clean_reddit(raw)
    if shape == "roomsurf":
        return cleaning.clean_roomsurf(raw)
    if shape == "niche":
        stats, reviews = cleaning.clean_niche(raw)
        return "[STATS]\n" + stats + "\n\n[REVIEWS]\n" + "\n\n".join(reviews)
    if shape == "list":
        return "\n".join(cleaning.clean_list(raw))
    if ext == ".html":
        return cleaning.clean_html(raw)
    return cleaning.clean_longform_txt(raw)


def main():
    by_name = {s["filename"]: s for s in manifest()}
    for shape, fn in SAMPLES.items():
        src = by_name[fn]
        cleaned = clean_for(src, load_raw(src))
        print("=" * 78)
        print(f"{shape.upper()}  —  {fn}   ({len(cleaned):,} chars)")
        print("-" * 78)
        print(cleaned[:700])
        print(" ...[TAIL]... ")
        print(cleaned[-300:])
        print()


if __name__ == "__main__":
    main()