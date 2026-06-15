from dotenv import load_dotenv
from config import LLM_MODEL, SYSTEM_PROMPT, GROQ_API_KEY, HYDE_PROMPT
from src.retrieval import retrieve
from textwrap import dedent

from groq import Groq

_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def generate_hypothetical(query: str) -> str:
    '''HyDE — draft a plausible answer passage to embed for retrieval.

    Dense retrieval matches question-shaped queries to question-shaped text,
    so terse answers rank low (see NOTES.md). Embedding a hypothetical *answer*
    instead pulls answer-shaped chunks up. The passage need not be factually
    correct — answer() still grounds strictly on the real retrieved chunks.

    Left deliberately "blind" (no corpus grounding): the model's own knowledge
    of real Towson places (e.g. Donnybrook, Aspen Heights) is often correct and
    helps retrieval. Grounding it on a first-pass retrieval was tried and
    REGRESSED the eval — it suppressed that beneficial prior knowledge (see
    NOTES.md, HyDE grounding experiment).

    Input:
        query: the user's natural-language question.
    Output:
        str — a short hypothetical answer passage (falls back to the original
        query if the LLM returns nothing).
    '''
    client = _get_groq_client()
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": HYDE_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )
    return completion.choices[0].message.content or query


def hyde_retrieve(query: str) -> list[dict]:
    '''Retrieve with HyDE by MERGING two searches: one on the raw query, one on
    a hypothetical answer. Deduped by chunk (source, chunk_index), best distance
    kept, sorted by distance.

    Two separate searches beat a single combined embedding: the query search
    keeps questions whose answer is a tight on-topic cluster (e.g. a whole
    complaint thread), while the hypothetical search surfaces terse answers a
    question-shaped query would bury. Union -> both survive. Stays at 2 local
    embeddings + 1 hypothetical LLM call.
    '''
    pooled = retrieve(query) + retrieve(generate_hypothetical(query))
    best = {}
    for h in pooled:
        key = (h["source"], h["chunk_index"])
        if key not in best or h["distance"] < best[key]["distance"]:
            best[key] = h
    return sorted(best.values(), key=lambda h: h["distance"])

def format_context(hits: list[dict]) -> str:
    '''Takes results from retrieve() and formats them for the LLM model.
    Input: list[dict] of text, source, type, subtopic, entity, chunk_index, and distance
    Output: Returns a string formatted:
    [chunk_id] (source_type(e.g, 'informal' or 'official'), source) (entity) (text).
    '''
    call_context = ""
    for idx, hit in enumerate(hits, start=1):
        ent = f" (entity: {hit['entity']}) " if hit.get('entity') else ""
        buf = f"[{idx}] ({hit['type']}, {hit['source']}){ent}text: {hit['text']}\n\n"
        call_context += buf
    return call_context

def answer(query, use_hyde=True):
    '''
    Run the full (RAG) generation step: retrieve grounding chunks, ask the LLM to answer questions directly from them,
    and attribute sources citations to the answers programmatically.

    Steps:
        1. If use_hyde, draft a hypothetical answer and retrieve with THAT;
           otherwise retrieve with the raw query. -> top-K_RESULTS chunks (hits)
        2. Call format_context(hits) -> labled context block for the prompt
        3. Call (LLM Model) with SYSTEM_PROMPT as the system message and the context + question as the user message.
        4. Build the citation list programmatically from hits (deduped, best-match order preserved) - NOT from the LLM's text.

        Input:
            query: the user's natural-language question
            use_hyde: if True, retrieve via a HyDE hypothetical answer (default);
                      set False to retrieve with the raw query (baseline).
        Output:
            dict with:
                "answer": - The LLM's grounded response text
                "sources": list[str] - unique source filenames cited, ranked in order
                "hits": list[dict] - the raw received chunks for debugging and UI.
    '''
    # HyDE: merge a query search with a hypothetical-answer search (both signals
    # survive); or the raw query alone (baseline). The FINAL answer always
    # grounds on `query`, never on the hypothetical.
    hits = hyde_retrieve(query) if use_hyde else retrieve(query)
    formatted_context = format_context(hits)

    client = _get_groq_client()

    user_message = f'Sources:\n{formatted_context}\n\n---\n\nUser query:\n{query}'.strip()

    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0
    )

    response = completion.choices[0].message.content

    sources = list(dict.fromkeys(h['source'] for h in hits))

    answer = response if response else "Sorry I couldn't generate an answer. Please try again."

    return {
        "answer": answer,
        "sources": sources,
        "hits": hits,
    }