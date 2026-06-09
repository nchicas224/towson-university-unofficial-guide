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

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
