# Findings & Divergences

Running log of things that diverged from `planning.md` or surfaced during
implementation. Raw material for the Milestone 6 evaluation report.

## Implementation diverged from plan

- **`MIN_CHARS = 30` chunk filter (Milestone 3).** Not in planning.md's
  Chunking Strategy. Added to drop low-signal fragments (one-word Reddit
  comments like "lmao", stray PDF page numbers) that would otherwise retrieve
  on surface words without carrying an answer. Took total chunks 423 -> 381.

## Retrieval findings (Milestone 4)

- **Eval result: 4/5 questions pass** (spec bar is >=3). Cosine distance,
  k=5, threshold < 0.5.

- **Q4 miss — "How many all-you-care-to-eat dining halls does Towson have?"**
  Expected source `locations_and_menus.txt` lands at **rank 14 (dist 0.501)**,
  pushed out of the top-5 by conversational dining chatter from Reddit/reviews.
  Root cause is *source content*, not the pipeline: the manually-copied
  CampusDish page came across as a bare **address directory** — it lists Glen,
  Newell, and West Village among many venues but never uses the phrase
  "all-you-care-to-eat" and never states the count "3". So the chunk is
  semantically "a list of addresses," far from the natural-language question.
  This is exactly the "fragmented / noisy chunks retrieve poorly" risk named in
  planning.md -> Anticipated Challenges #3 (vocabulary mismatch).
  **Decision:** left as-is and documented (honest RAG limitation). Could be
  fixed later by re-copying the page's "all-you-care-to-eat" framing or adding a
  one-line header naming the 3 halls, then re-embedding.

- **Q2 strength.** "Freshman car / parking" retrieved both the student Reddit
  thread *and* the official PDF in the top-5 (top dist 0.125) — the
  official-vs-informal blend planning.md -> Anticipated Challenges #1 wanted.
