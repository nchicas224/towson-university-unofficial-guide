"""Stage 4 test — run the evaluation questions through retrieval.

Checks (per planning.md -> Evaluation Plan / AI Tool Plan Milestone 4):
  - the expected source(s) appear in the top-k
  - top distance is below ~0.5 (on-topic), flagged if not

Assumes the index exists (run `python -m src.embed_store` first).
Run from the repo root:  python -m src.inspect_retrieval
"""

from src.retrieval import K, retrieve

GOOD = 0.5  # cosine-distance threshold for "on-topic" (planning.md)

# (question, set of source filenames we expect to see in the top-k)
EVAL = [
    ("What changed about Towson's campus dining after Aramark took over, "
     "and how did it affect students?",
     {"dinning_halls.json"}),
    ("Can a freshman bring a car to campus at Towson, and what happens if "
     "you park without a permit?",
     {"parking-regulations.pdf", "parking_at_towson.json"}),
    ("Which off-campus apartment complexes do students recommend for transfers "
     "wanting a 2-bed/2-bath near campus?",
     {"transfer_student_fall_26_housing_advice.json"}),
    ("How many all-you-care-to-eat dining halls does Towson have, "
     "and what are they?",
     {"locations_and_menus.txt"}),
    ("Which freshman dorm is considered the most central/convenient, "
     "and what's the main drawback?",
     {"freshman_dorm_ranking.txt", "dorm_reviews.txt", "niche_campus_life.txt"}),
]


def main():
    passed = 0
    for i, (q, expected) in enumerate(EVAL, 1):
        hits = retrieve(q, k=K)
        got_sources = {h["source"] for h in hits}
        top = hits[0]["distance"]
        hit_expected = bool(got_sources & expected)
        on_topic = top < GOOD
        ok = hit_expected and on_topic
        passed += ok

        print("=" * 80)
        print(f"Q{i}  [{'PASS' if ok else 'CHECK'}]  top_distance={top:.3f}"
              f"  expected_source_hit={hit_expected}")
        print(f"  {q}")
        print(f"  expected one of: {sorted(expected)}")
        print("-" * 80)
        for h in hits:
            mark = "*" if h["source"] in expected else " "
            ent = f"  entity={h['entity']}" if h["entity"] else ""
            print(f"  {mark} {h['distance']:.3f}  {h['type']:<8} {h['source']:<42}"
                  f"{ent}")
            print(f"        {h['text'][:100].strip()}")
        print()

    print("=" * 80)
    print(f"SUMMARY: {passed}/{len(EVAL)} questions retrieved an expected source "
          f"with top distance < {GOOD}")


if __name__ == "__main__":
    main()
