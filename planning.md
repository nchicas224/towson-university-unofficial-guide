# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
This project will build an unofficial guide for Towson University students focused on student life, including campus dining, dorms, off-campus housing, and general campus survival advice. The system will combine official university information with informal student experiences from public reviews, Reddit threads, and other student-facing sources.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

All nav-hub URLs have been resolved to leaf pages that carry real content. The **Fetch method** column drives the ingestion script (Milestone 3) — four loader branches: Reddit `.json` parse, HTML strip, PDF extract (`pdfplumber`), and manual copy for JS-rendered sites.

| # | Source | Subtopic | Type | Description | URL or location | Fetch method |
|---|--------|----------|------|-------------|-----------------|--------------|
| 1 | Reddit: "Best dining hall?" | dining | informal | Student opinions comparing West, Newell, Glen, and other dining options. | https://www.reddit.com/r/Towson/comments/x1l8tv/best_dining_hall/.json | Reddit `.json` |
| 2 | Reddit: "Dinning halls" | dining | informal | Frustration over the Aramark takeover — worse meal plans, grill changes, quality drop. 15 comments. | documents/dinning_halls.json | JSON (saved) |
| 3 | CampusDish — Meal Plans | dining | official | Meal plan tiers, swipes, dining dollars — the authoritative "how it works." | https://towson.campusdish.com/MealPlans | Manual copy (JS) |
| 4 | CampusDish — Locations & Menus | dining | official | The 3 all-you-care-to-eat halls (Glen, Newell, West Village) + named venues/menus. | https://towson.campusdish.com/LocationsAndMenus | Manual copy (JS) |
| 5 | Reddit: "Parking at Towson" | parking / survival | informal | Freshman trying to dodge the no-car rule; ticket odds, patrol patterns, free parking nearby. 19 comments. | documents/parking_at_towson.json | JSON (saved) |
| 6 | TU Parking Regulations 2025/26 | parking / survival | official | Full permit/enforcement/penalty policy incl. freshman (<30 units) no-car rule. ~100% content. | https://www.towson.edu/parking/documents/parking-regulations.pdf | PDF (pdfplumber) |
| 7 | Reddit: "Transfer student Fall 26 housing advice" | off-campus | informal | Apartment recs for transfers (Donnybrook, Aspen Heights, York) with pros/cons. 18 comments. | documents/transfer_student_fall_26_housing_advice.json | JSON (saved) |
| 8 | TU Off-Campus — Before You Rent | off-campus | official | Practical pre-lease rental guidance (the substance the off-campus hub linked out to). | https://www.towson.edu/studentlife/housing/offcampus/beforerent/index.html | HTML strip |
| 9 | TU Off-Campus — After You Move In | off-campus | official | Tenant guidance after signing/moving in. | https://www.towson.edu/studentlife/housing/offcampus/aftermove/index.html | HTML strip |
| 10 | Society19: Freshman Dorm Ranking | dorms | informal | Opinionated freshman dorm ranking (e.g. The Towers — central but slow elevators). | https://www.society19.com/the-ultimate-ranking-of-freshman-dorms-at-towson-university/ | Manual copy |
| 11 | Roomsurf: Towson Dorm Reviews | dorms | informal | Crowd-sourced per-dorm star ratings and short reviews. | https://www.roomsurf.com/dorm-reviews/towson | Manual copy |
| 12 | TU Glen Complex (official) | dorms | official | Official layout/amenities for Glen Towers — factual baseline for the "Towers" student opinions. | https://www.towson.edu/studentlife/housing/campus/residence/glen.html | HTML strip |
| 13 | Niche: Towson Campus Life | survival | informal | Aggregated student reviews on safety, food, party scene, parking, "commuter school" weekends. | https://www.niche.com/colleges/towson-university/campus-life/ | Manual copy |
| 14 | TU Resources for Residents | survival | official | Mildew/mold prevention tips + Fall Triples policy (20% refund, de-tripled by spring) + contacts. | https://www.towson.edu/studentlife/housing/campus/resources/ | HTML strip |
| 15 | TU Packing Guide | survival | official | What to bring / leave behind when moving into a residence hall. | https://www.towson.edu/studentlife/housing/campus/resources/packing.html | HTML strip |
| 16 | TU Housing Policies | survival | official | Official residence-hall policies (rules, conduct, what's allowed). | https://www.towson.edu/studentlife/housing/campus/resources/policies.html | HTML strip |

> Dropped from earlier draft: the **OneCard/jsatech meal portal** (login wall, no public content) and the **off-campus housing search app** (dynamic listings, no static text). Both are interactive apps, not documents.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
Three document shapes, each chunked to fit its structure:
- **Atomic short units** (~20–150 words, self-contained) — Reddit JSONs, Roomsurf reviews, Niche reviews → one chunk per comment/review, kept whole.
- **Continuous long-form** — parking PDF, housing_policies, packing_guide, before/after_rent, glen_complex, freshman_ranking → split on paragraph breaks, then cap and recursively sub-split anything over the target.
- **Structured lists** — meal_plans, locations_and_menus → one record per chunk.

Target size: **~800 characters (~200 tokens / ~150 words)**. Natural units under the target are kept whole; only long-form sections that exceed it are sub-split (RecursiveCharacterTextSplitter).

**Overlap:**
**~100 characters (~15%, roughly one sentence)** on long-form splits, so a fact isn't severed at a boundary. **Zero overlap** on atomic review chunks — they're independent, so overlap would only duplicate content and waste embeddings.

**Metadata** (attached to every chunk at split time):
- `source` — filename, for attribution (required by Milestone 4)
- `type` — official | informal (lets us weigh student voice vs. policy)
- `subtopic` — dining | parking | dorms | off-campus | survival
- `entity` — reviews only: the specific dorm/place (e.g. "Glen Tower B")
- `chunk_index` — position within the source document

`type` and `subtopic` mirror the columns in the Documents table above; `entity` enables the Metadata Filtering stretch feature.

**Reasoning:**
The corpus has two fundamentally different shapes, so no single fixed size serves both. A Reddit comment or Roomsurf review is already a complete, self-contained thought with a natural author boundary — e.g. "Lots of mold too. I was constantly sick when I had a dorm here." Splitting it is destructive, and merging two reviewers into one chunk is worse: it blends conflicting opinions and destroys attribution. A policy PDF or packing guide, by contrast, is continuous prose where a single fact can span a paragraph ("freshmen under 30 units can't have a car"), so sentences should stay grouped and a fact shouldn't be severed at a boundary. A single fixed-size splitter (split every 500 chars) serves neither — it fuses three separate Reddit comments and bisects a policy clause, the exact failure the spec warns about ("All chunks the same length → splitting mechanically without respecting content boundaries").

The hard ceiling on chunk size is the embedding model: **all-MiniLM-L6-v2 has a max sequence length of 256 tokens (~190 words)**, beyond which the tail is silently truncated and never embedded — a "500-token chunk" would lose half its meaning invisibly. That's why the target sits comfortably under 256 tokens, at ~800 characters.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
`all-MiniLM-L6-v2` via `sentence-transformers`. Runs locally, no API key or rate limits, and is well-suited to short semantic-similarity tasks — which fits a corpus dominated by short review/comment chunks. Its 256-token max sequence length is the constraint that caps our chunk size (see Chunking Strategy).

**Top-k:**
Start at **k=5**. The corpus deliberately mixes official and informal sources on the same topic, so we want enough chunks to surface *both* voices for a query (e.g. the parking policy *and* the student ticket experience). We'll tune after seeing real retrieval in Milestone 4 — too low and the relevant chunk may be excluded; too high and loosely-related chunks dilute the LLM context.

**Production tradeoff reflection:**
If cost weren't a constraint, the main tradeoffs to weigh against a different model:
- **Context length** — MiniLM's 256-token ceiling forces us to split long-form policy text and silently truncates anything we miss. A larger-context embedding model (e.g. OpenAI `text-embedding-3-large`, Voyage, or `bge-large`) would let long-form chunks stay whole, reducing boundary-severing failures.
- **Accuracy on domain-specific text** — our informal sources are full of slang, typos, and Towson-specific names ("Tu Cribs," "West Privilege," dorm nicknames). A larger model generally embeds this messy text more robustly.
- **Latency / local vs. API** — MiniLM is fast and free locally; an API model adds per-call cost and network latency but offloads compute.
- **Multilingual** — not relevant here; our corpus is English-only, so we'd gain nothing from a multilingual model.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What changed about Towson's campus dining after Aramark took over, and how did it affect students? | Meal plans became more restrictive/worse, you can no longer custom-order at the grills, overall food quality dropped, and students feel forced into the dining halls. (Source: `dinning_halls.json`) |
| 2 | Can a freshman bring a car to campus at Towson, and what happens if you park without a permit? | Freshman residents (under 30 earned units) are **not** allowed to buy a permit or have a car on campus; parking without a valid permit gets you ticketed — patrol cars cycle the garages every 1–2 hours reading plates against a database. (Sources: `parking-regulations.pdf`, `parking_at_towson.json`) |
| 3 | Which off-campus apartment complexes do students recommend for transfers wanting a 2-bed/2-bath near campus? | Donnybrook, Aspen Heights, and York. (Source: `transfer_student_fall_26_housing_advice.json`) |
| 4 | How many all-you-care-to-eat dining halls does Towson have, and what are they? | Three: The Glen, Newell Dining Hall, and West Village Commons. (Sources: `locations_and_menus.txt`, CampusDish) |
| 5 | Which freshman dorm is considered the most central/convenient, and what's the main drawback? | The Towers (Glen Complex) — in the heart of campus, easy to reach classes/dining — but the elevators are notoriously slow. (Sources: `freshman_dorm_ranking.txt`, `dorm_reviews.txt`, `niche_campus_life.txt`) |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Official and student sources conflict on the same query.** Question 2 (parking) is the clearest case: the official PDF states the no-freshman-car rule, while the Reddit thread is about *dodging* it. Retrieval might surface only one voice, or the LLM might present a student rant as authoritative policy. Mitigation: retrieve enough chunks (k=5) to span both, carry the `type` (official/informal) metadata, and instruct the generator to distinguish "official policy" from "what students say."

2. **Near-duplicate content crowds out the top-k.** We already found a duplicated dorm review and triplicated meal-plan blocks, and the per-dorm reviews repeat similar sentiment ("close to dining," "friendly staff," "felt safe"). Several near-identical chunks can fill the top-k and starve the answer of other relevant info. Mitigation: the dedup we did, plus `entity` metadata so we can tell which dorm each review is actually about.

3. **Fragmented / noisy chunks retrieve poorly.** The Niche poll data is split into label/value lines ("Average Housing Cost" / "$8,502 per year") that lose meaning once chunked, and short Reddit fragments may match a query on surface words without carrying a real answer — the classic low-signal retrieval failure.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DOCUMENT INGESTION                                                 │
│    4 loader branches by fetch method:                                 │
│    .json (Reddit) → selftext + comment bodies                         │
│    .html (TU pages) → strip tags/nav  (BeautifulSoup)                 │
│    .pdf (parking)  → extract text     (pdfplumber)                    │
│    .txt (JS sites) → already clean                                    │
└───────────────────────────────┬───────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. CHUNKING  (boundary-aware, ~800 chars / ~100 overlap)              │
│    atomic units → 1 chunk/review · long-form → paragraph + recursive  │
│    split (RecursiveCharacterTextSplitter) · attach metadata           │
│    {source, type, subtopic, entity, chunk_index}                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. EMBEDDING + VECTOR STORE                                           │
│    all-MiniLM-L6-v2 (sentence-transformers) → ChromaDB (+ metadata)   │
└───────────────────────────────┬───────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. RETRIEVAL   query → embed → top-k=5 semantic search (ChromaDB)     │
└───────────────────────────────┬───────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. GENERATION   Groq llama-3.3-70b-versatile                          │
│    grounded prompt (answer ONLY from retrieved chunks) + source       │
│    attribution appended programmatically                              │
│    Interface: Gradio web UI                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
Tool: Claude. Input: the Documents table (with the Fetch method column) + the Chunking Strategy section + the architecture diagram. Ask it to implement a loader with the four branches (`.json`/`.html`/`.pdf`/`.txt`) and a `chunk_text()` that keeps atomic units whole, paragraph-splits + recursively sub-splits long-form to ~800 chars with ~100 overlap, and attaches the five metadata fields. Verify by printing 5 representative chunks (one per source shape) and checking: no HTML/footer artifacts, no chunk over ~256 tokens, reviews not merged across authors, metadata correct. Confirm total chunk count lands in the 50–2,000 range.

**Milestone 4 — Embedding and retrieval:**
Tool: Claude. Input: the Retrieval Approach section + the architecture diagram. Ask it to embed all chunks with `all-MiniLM-L6-v2`, store them in ChromaDB with metadata, and write a `retrieve(query, k=5)` that returns chunks + sources + distance scores. Verify by running at least 3 of the 5 evaluation questions and checking the returned chunks are on-topic with distance scores below ~0.5 — debugging chunk size before adding generation if not.

**Milestone 5 — Generation and interface:**
Tool: Claude. Input: the architecture diagram + grounding requirement. Ask it to write a prompt template that instructs the LLM (Groq `llama-3.3-70b-versatile`) to answer **only** from retrieved chunks and to say so when the context is insufficient, append source attribution programmatically (not LLM-generated), and wrap it in a Gradio UI. Verify by running the 5 evaluation questions end-to-end + one out-of-scope question, confirming answers are traceable to retrieved chunks, sources are cited, and the out-of-scope query produces a refusal rather than a hallucination.
