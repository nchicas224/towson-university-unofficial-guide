"""Source manifest — mirrors the Documents table in planning.md.

Each entry records the metadata we attach to every chunk (type, subtopic) plus
the `shape`, which selects the chunking strategy:
  - "reddit"   : Reddit .json — one chunk per post/comment (atomic)
  - "roomsurf" : Roomsurf reviews .txt — one chunk per review (atomic)
  - "niche"    : Niche .txt — atomic reviews + a stats preamble
  - "longform" : HTML / PDF / article prose — paragraph + recursive split
  - "list"     : structured records (.txt) — one record per chunk
"""

from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"

# fmt: off
SOURCES = [
    # filename                                          type        subtopic      shape
    ("best_dining_halls.json",                          "informal", "dining",     "reddit"),
    ("dinning_halls.json",                              "informal", "dining",     "reddit"),
    ("parking_at_towson.json",                          "informal", "parking",    "reddit"),
    ("transfer_student_fall_26_housing_advice.json",    "informal", "off-campus", "reddit"),
    ("meal_plans.txt",                                  "official", "dining",     "list"),
    ("locations_and_menus.txt",                         "official", "dining",     "list"),
    ("freshman_dorm_ranking.txt",                       "informal", "dorms",      "longform"),
    ("dorm_reviews.txt",                                "informal", "dorms",      "roomsurf"),
    ("niche_campus_life.txt",                           "informal", "survival",   "niche"),
    ("before_you_rent.html",                            "official", "off-campus", "longform"),
    ("after_you_move_in.html",                          "official", "off-campus", "longform"),
    ("glen_complex.html",                               "official", "dorms",      "longform"),
    ("housing_policies.html",                           "official", "survival",   "longform"),
    ("packing_guide.html",                              "official", "survival",   "longform"),
    ("resources_for_residents.html",                    "official", "survival",   "longform"),
    ("parking-regulations.pdf",                         "official", "parking",    "longform"),
]
# fmt: on


def manifest():
    """Yield dicts of source metadata, with an absolute path attached."""
    for filename, type_, subtopic, shape in SOURCES:
        yield {
            "filename": filename,
            "path": DOCUMENTS_DIR / filename,
            "type": type_,
            "subtopic": subtopic,
            "shape": shape,
        }
