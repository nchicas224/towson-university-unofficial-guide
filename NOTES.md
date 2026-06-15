# Findings & Divergences

Running log of things that diverged from `planning.md` or surfaced during
implementation. Raw material for the Milestone 6 evaluation report.

## Implementation diverged from plan

- **`MIN_CHARS = 30` chunk filter (Milestone 3).** Not in planning.md's
  Chunking Strategy. Added to drop low-signal fragments (one-word Reddit
  comments like "lmao", stray PDF page numbers) that would otherwise retrieve
  on surface words without carrying an answer. Took total chunks 423 -> 381.

## Retrieval / end-to-end findings (Milestones 4-5)

- **Two ways to score the eval, and they disagree badly:**
  - *Source-level retrieval* (inspect_retrieval.py): **4/5 pass** — "did an
    expected source filename appear in the top-5, top dist < 0.5".
  - *End-to-end generation* (the real test): **2/5 fully answered** — only Q1
    and Q2. Q3, Q4, Q5 produce honest "I couldn't find that" refusals.
  The gap is large because the source-level metric **over-counts**: for Q3 and
  Q5 the expected source appears in the top-5, but via a chunk that is NOT the
  answer (Q3's #1 hit is the original *post/question*; Q5's is the article
  *intro*). The answer-bearing chunks rank far lower. Lesson: judge a RAG
  system end-to-end, not on source recall alone.

- **Root cause unifying the 3 misses: dense retrieval is asymmetric +
  answers aren't always localized.**
  - **Q3 "Which apartments do students recommend?"** — clearest case. Expected
    source ranks #1, but the #1 chunk is the *post* ("my friend and I are
    transferring, any recs?"), which matches the question-shaped query far
    better than the terse answer comments ("I wanna say Donnybrook or aspen
    heights or even York"). The apartment-naming comments rank **21, 34, 77,
    78, 181 / 381** — nowhere near the top-5. A question-shaped query pulls
    question-shaped text to the top and buries the answers. Bumping k won't fix
    it cleanly (rank 21+).
  - **Q4 / Q5 — aggregative & superlative.** Answer not localized in one chunk:
    Q4 "*how many* halls total" (no chunk states "3"; expected
    `locations_and_menus.txt` is a bare address directory, rank 14 / 0.501).
    Q5 "*most* central dorm" — answer chunks exist ("heart of campus" /
    "elevators... so slow") but rank **60 & 64 / 381 (~0.54)**; "most central"
    also needs cross-dorm comparison no single chunk supports.

- **Q4 + Q5 are the same failure mode: aggregative / superlative questions.**
  Dense single-chunk retrieval is structurally weak when the answer is not
  localized in one chunk:
  - **Q4 "How *many* all-you-care-to-eat halls *total*?"** — a count. No chunk
    states "3". Expected `locations_and_menus.txt` is a bare address directory
    (lists Glen/Newell/West Village among many venues, never says
    "all-you-care-to-eat" or "3"); it lands at **rank 14 (0.501)**.
  - **Q5 "Which dorm is the *most* central, main drawback?"** — a superlative +
    comparison. The answer-bearing chunks DO exist in
    `freshman_dorm_ranking.txt` ("The Towers are right in the heart of campus" /
    "the only bad thing... the elevators... so slow") but rank **60 & 64 / 381
    (dist ~0.54)** — vocabulary gap ("most central" vs "heart of campus",
    "drawback" vs "the only bad thing") plus per-paragraph signal dilution.
    Answering "*most* central" also requires comparing across dorms, which no
    single chunk supports.
  This is planning.md -> Anticipated Challenges #3 (fragmented/vocabulary
  mismatch) made concrete, plus a class the plan didn't name: counting/superlative
  questions.
  **Decision:** left as-is and documented (honest RAG limitation; the model
  refuses rather than fabricates, which is correct behavior). Possible future
  fixes: query expansion/HyDE, a larger-context embedding model so paragraphs
  stay whole, or adding a source that states the count/comparison explicitly.

- **Q2 strength.** "Freshman car / parking" retrieved both the student Reddit
  thread *and* the official PDF in the top-5 (top dist 0.125), and generation
  cleanly separated "official policy: not allowed" from "some students say
  overflow permits" — the official-vs-informal blend planning.md ->
  Anticipated Challenges #1 wanted.

## HyDE stretch feature (Milestone 5) — 2/5 -> 3/5

Added Hypothetical Document Embeddings to fix the asymmetric-retrieval misses.
`generate_hypothetical()` (src/generation.py) drafts a plausible answer; the
final answer() still grounds strictly on the real retrieved chunks. Tried three
variants, measured end-to-end on all 5 eval questions:

| Variant | Q1 | Q2 | Q3 | Q4 | Q5 | net |
|---------|----|----|----|----|----|-----|
| Baseline (raw query)          | OK | OK | -- | -- | -- | 2/5 |
| Pure HyDE (embed hypo only)   | -- | OK | OK | -- | -- | 2/5 |
| Concat (query + hypo)         | OK | OK | -- | -- | -- | 2/5 |
| **Merge (query U hypo)** **(chosen)** | OK | OK | OK | -- | -- | **3/5** |

- **Why pure HyDE traded Q1 for Q3:** embedding only the hypothetical throws
  away the literal query terms. Q3 (terse answers) improves; Q1 (answer is a
  tight on-topic thread the *query* matched well) regresses. Concatenation had
  the same net problem — one embedding can't hold both signals in the top-5.
- **Why merge wins:** run TWO searches (raw query + hypothetical), dedup by
  (source, chunk_index), keep best distance. Query-side keeps Q1's thread;
  hypothesis-side surfaces Q3's buried comments. Both survive -> 3/5, no
  regression. Cost: 2 LLM calls + 2 retrievals per query (acceptable for demo).
  `answer(query, use_hyde=True)` is the default; pass False for the baseline.
- **Q3 fixed:** hypothetical captured the right *vocabulary* ("students
  recommend complexes ... 2-bed/2-bath near campus"); the real answer comments
  (Towson Place, University Village, DonnyBrook) now retrieve.
- **Q4 still fails (fundamental):** "how many ... total" — the count "3" is not
  stated in ANY chunk; the model correctly won't fabricate it.
- **Q5 still fails (HyDE backfire):** the hypothetical *hallucinated a
  nonexistent dorm* ("Richmond Hall ... noisy ... scarce parking"), steering
  retrieval to the wrong vocabulary. The real answer chunks ("The Towers are
  right in the heart of campus" / "elevators ... so slow") stay buried. HyDE
  helps when it guesses the right general vocabulary (Q3) and hurts when it
  commits to a wrong specific entity (Q5). Also a superlative needing
  cross-dorm comparison no single chunk supports.

### Grounded-HyDE experiment — tried, REVERTED (3/5 -> 2/5)

To stop the Q5 fabrication, tried grounding the hypothetical on a first-pass
`retrieve(query)` (feed real excerpts into the HyDE prompt + a "use only names
in the excerpts, do not invent" guard). Cost-free in principle: reuses the
query retrieval already needed for the merge, no extra LLM call.

Result: it killed the fabrication (Q5 hypothetical became honest) but
**regressed Q3 from pass to fail**, netting 2/5 — worse than blind HyDE. Why:
- **Q3's win was the model's *correct prior knowledge*.** Donnybrook / Aspen
  Heights are real Towson-area complexes the model knew from training. The
  "don't invent names" guard can't tell beneficial real-knowledge from harmful
  invention, so it suppressed both — and Q3's first-pass retrieval doesn't
  contain the apartment names (buried at rank 21+), so grounding had no real
  names to offer; it just gagged the model into a generic, useless passage.
- **Fixing Q5's fabrication bought nothing** — Q5 was failing anyway (answer
  chunks stay buried + superlative). We cured a symptom that wasn't costing a
  passing question and broke one that depended on good priors.

**Lesson (for the report):** a principled-sounding fix (ground the hypothetical
to prevent hallucination) lost to the messy one on this corpus, because the
hardest asymmetric cases need vocabulary that *isn't yet in* the first-pass
retrieval — exactly what grounding restricts you to. Kept blind merge-HyDE
(3/5). `generate_hypothetical()` retains a comment pointing here.
