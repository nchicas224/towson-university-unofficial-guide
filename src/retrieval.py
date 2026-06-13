"""Stage 4 — Retrieval.

Embeds a query with the same model used to build the index and runs a top-k
cosine similarity search against the ChromaDB collection (see planning.md ->
Retrieval Approach: k=5, cosine distance, judged on-topic when distance < ~0.5).

    from src.retrieval import retrieve
    hits = retrieve("can a freshman bring a car to campus?", k=5)
    for h in hits:
        print(h["distance"], h["source"], h["text"][:80])
"""

from src.embed_store import get_collection, get_model
from config import K_RESULTS


def retrieve(query: str, k: int = K_RESULTS, where: dict | None = None):
    """Return the top-k chunks for a query as a list of dicts:
        {text, source, type, subtopic, entity, chunk_index, distance}
    `where` is an optional ChromaDB metadata filter, e.g. {"subtopic": "parking"}
    (this is the hook for the metadata-filtering stretch feature)."""
    model = get_model()
    collection = get_collection()

    query_emb = model.encode([query]).tolist()
    res = collection.query(
        query_embeddings=query_emb,
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "type": meta["type"],
            "subtopic": meta["subtopic"],
            "entity": meta["entity"] or None,
            "chunk_index": meta["chunk_index"],
            "distance": dist,
        })
    return hits
