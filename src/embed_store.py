"""Stage 3+4 — Embedding + Vector Store.

Embeds every chunk from build_chunks() with all-MiniLM-L6-v2 and stores the
vectors + metadata in a persistent ChromaDB collection (see planning.md ->
Retrieval Approach + Architecture stage 3).

Run from the repo root to (re)build the index:
    python -m src.embed_store
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.chunking import build_chunks
from config import CHROMA_COLLECTION, EMBEDDING_MODEL, CHROMA_PATH

PERSIST_DIR = Path(__file__).resolve().parent.parent / CHROMA_PATH

# Cosine distance (1 - cosine similarity): range 0-2, good matches < ~0.5.
# This is the threshold planning.md's Evaluation Plan judges retrieval against.
_SPACE = {"hnsw:space": "cosine"}

_model = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (it's ~80 MB)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(PERSIST_DIR))


def get_collection(create: bool = False):
    """Return the collection. With create=True, drops and rebuilds it."""
    client = get_client()
    if create:
        try:
            client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass  # didn't exist yet
        return client.create_collection(CHROMA_COLLECTION, metadata=_SPACE)
    return client.get_collection(CHROMA_COLLECTION)


def _to_metadata(chunk: dict) -> dict:
    """Chroma metadata values must be str/int/float/bool — no None.
    `entity` is None for everything except reviews, so fold it to ""."""
    return {
        "source": chunk["source"],
        "type": chunk["type"],
        "subtopic": chunk["subtopic"],
        "entity": chunk["entity"] or "",
        "chunk_index": chunk["chunk_index"],
    }


def build_index():
    """Embed all chunks and (re)write the ChromaDB collection from scratch."""
    chunks = build_chunks()
    model = get_model()

    texts = [c["text"] for c in chunks]
    # all-MiniLM normalizes nothing by default; ChromaDB's cosine space handles
    # the normalization, so we just hand it raw embeddings.
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    # IDs must be unique: source + chunk_index is (source resets index per file).
    ids = [f"{c['source']}::{c['chunk_index']}" for c in chunks]
    metadatas = [_to_metadata(c) for c in chunks]

    collection = get_collection(create=True)
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    return collection


def main():
    collection = build_index()
    count = collection.count()
    print(f"Indexed {count} chunks into '{CHROMA_COLLECTION}' at {PERSIST_DIR}")
    # quick sanity: record at 15 stored records
    results = collection.get(limit=15)
    records = zip(results['ids'], results['metadatas'], results['documents'])
    for record_id, metadata, document in records:
        print("\nsample stored record:")
        print("  id:      ", record_id)
        print("  metadata:", metadata)
        print("  text:    ", document[:120], "...")


if __name__ == "__main__":
    main()
