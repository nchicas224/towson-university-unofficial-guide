"""Stage 1 test — load every source and report what came off disk.

Run from the repo root:  python -m src.inspect_loading
"""

from src.loaders import load_raw
from src.sources import manifest


def count_reddit_units(data) -> int:
    """Post + all comments (including nested replies)."""
    def walk(children):
        n = 0
        for ch in children:
            if ch.get("kind") != "t1":
                continue
            n += 1
            replies = ch["data"].get("replies")
            if isinstance(replies, dict):
                n += walk(replies["data"]["children"])
        return n

    post = 1 if data[0]["data"]["children"] else 0
    return post + walk(data[1]["data"]["children"])


def main():
    print(f"{'filename':<46} {'shape':<9} {'size':>8}  detail")
    print("-" * 90)
    for src in manifest():
        raw = load_raw(src)
        if src["shape"] == "reddit":
            detail = f"{count_reddit_units(raw)} units (post+comments)"
            size = "json"
        else:
            size = f"{len(raw):,}"
            snippet = " ".join(raw.split())[:60]
            detail = repr(snippet)
        print(f"{src['filename']:<46} {src['shape']:<9} {size:>8}  {detail}")


if __name__ == "__main__":
    main()
