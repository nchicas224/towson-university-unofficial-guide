from dotenv import load_dotenv
from config import SYSTEM_PROMPT, GROQ_API_KEY

from groq import Groq

_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client

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

def answer(query):
    '''
    TODO
    '''
    pass