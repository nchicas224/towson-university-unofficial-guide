"""The Unofficial Guide — Gradio web app (Milestone 5, interface half).

Thin UI over the RAG pipeline: a chat box calls answer() (src/generation.py),
which retrieves grounding chunks, asks Groq to answer strictly from them, and
returns {answer, sources, hits}. This file just renders that.

Run from the repo root:  python app.py
"""

import gradio as gr

from config import CHROMA_COLLECTION
from src.embed_store import build_index, get_client
from src.generation import answer


# ---------------------------------------------------------------------------
# Ingestion — runs once on startup
# ---------------------------------------------------------------------------

def run_ingestion():
    """Build the vector store if it isn't already populated.

    If the collection exists with chunks, ingestion is skipped. To re-ingest
    (e.g. after changing chunking), delete the ./chroma_db folder and restart,
    or run `python -m src.embed_store` directly.
    """
    try:
        collection = get_client().get_collection(CHROMA_COLLECTION)
        if collection.count() > 0:
            print(f"Vector store already populated "
                  f"({collection.count()} chunks). Skipping ingestion.")
            return
    except Exception:
        pass  # collection doesn't exist yet — build it below

    print("Building vector store (embedding all chunks)...")
    collection = build_index()
    print(f"Ingestion complete. {collection.count()} chunks stored.")


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def chat(message, history):
    """Answer one question and append programmatic source attribution.

    The sources line is built from answer()'s `sources` (derived from the
    retrieved chunks in code) — never from the LLM's own text — so citations
    are always traceable to what was actually retrieved.
    """
    if not message.strip():
        return ""
    result = answer(message)
    text = result["answer"]
    if result["sources"]:
        cites = ", ".join(result["sources"])
        text += f"\n\n---\n*Sources: {cites}*"
    return text


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="amber", secondary_hue="yellow"),
    title="The Unofficial Guide",
) as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#000000; margin:0;">
                🐯 The Unofficial Guide
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Real talk on Towson student life — dining, dorms, housing,
                parking & survival. Official policy <em>and</em> what students
                actually say.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chat,
                type="messages",
                chatbot=gr.Chatbot(
                    height=460,
                    type="messages",
                    placeholder=(
                        "<div style='text-align:center; color:#9ca3af; "
                        "margin-top:3rem;'>Ask about dorms, dining, parking, "
                        "or off-campus housing to get started 🎓</div>"
                    ),
                ),
                textbox=gr.Textbox(
                    placeholder='e.g. "Can a freshman bring a car to campus?"',
                    container=False,
                    scale=7,
                ),
                examples=[
                    "What changed about Towson's dining after Aramark took over?",
                    "Can a freshman bring a car to campus, and what happens if "
                    "you park without a permit?",
                    "Which off-campus apartments do students recommend for "
                    "transfers wanting a 2-bed/2-bath near campus?",
                    "How many all-you-care-to-eat dining halls does Towson have?",
                    "Which freshman dorm is the most central, and what's the "
                    "main drawback?",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=190):
            gr.HTML("""
                <div style="background:#fffbeb; border:1px solid #fde68a;
                            border-radius:10px; padding:1rem; margin-top:0.5rem;">
                    <p style="font-size:0.8rem; font-weight:700; color:#78350f;
                               margin:0 0 0.5rem; letter-spacing:0.05em;">
                        📚 WHAT IT KNOWS
                    </p>
                    <ul style="font-size:0.85rem; color:#92400e; list-style:none;
                                padding:0; margin:0; line-height:1.8;">
                        <li>🍽️ Dining halls & meal plans</li>
                        <li>🏠 Dorms & residence life</li>
                        <li>🏢 Off-campus housing</li>
                        <li>🚗 Parking & permits</li>
                        <li>🧭 Campus survival</li>
                    </ul>
                    <hr style="border:none; border-top:1px solid #fde68a;
                               margin:0.75rem 0;">
                    <p style="font-size:0.75rem; color:#b45309; margin:0;
                               line-height:1.5;">
                        Answers come only from the loaded sources, with official
                        policy and student opinions kept distinct. If something
                        isn't covered, the guide will say so.
                    </p>
                </div>
            """)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  The Unofficial Guide — starting up")
    print("=" * 50 + "\n")
    run_ingestion()
    demo.launch()
