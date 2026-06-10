"""Stage 3 test — build all chunks, inspect quality and counts.

Run from the repo root:  python -m src.inspect_chunks
"""

from collections import Counter

from src.chunking import TARGET, build_chunks


def main():
    chunks = build_chunks()
    n = len(chunks)

    # --- counts & size sanity -------------------------------------------------
    per_source = Counter(c["source"] for c in chunks)
    lengths = [len(c["text"]) for c in chunks]
    empty = [c for c in chunks if not c["text"].strip()]
    oversize = [c for c in chunks if len(c["text"]) > TARGET + OVERLAP_SLACK]

    print(f"TOTAL CHUNKS: {n}   (target window 50–2,000)")
    print(f"length: min={min(lengths)}  max={max(lengths)}  "
          f"avg={sum(lengths)//n}  empty={len(empty)}  oversize={len(oversize)}")
    print("\nper-source chunk counts:")
    for src, cnt in per_source.items():
        print(f"  {src:<46} {cnt}")

    # --- 5 representative chunks (one per shape family) -----------------------
    picks, seen_sources = [], set()
    want = ["parking_at_towson.json", "dorm_reviews.txt", "niche_campus_life.txt",
            "meal_plans.txt", "parking-regulations.pdf"]
    for fn in want:
        for c in chunks:
            if c["source"] == fn:
                picks.append(c)
                break

    print("\n" + "=" * 78)
    print("5 REPRESENTATIVE CHUNKS")
    for c in picks:
        print("=" * 78)
        print(f"source={c['source']}  type={c['type']}  subtopic={c['subtopic']}  "
              f"entity={c['entity']}  idx={c['chunk_index']}  len={len(c['text'])}")
        print("-" * 78)
        print(c["text"][:600])


OVERLAP_SLACK = 50  # allow a little slack over TARGET for clean sentence breaks

if __name__ == "__main__":
    main()