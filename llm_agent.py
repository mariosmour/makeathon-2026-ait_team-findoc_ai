import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

load_dotenv()


SYSTEM_PROMPT = """
Είσαι AI agent για ερωτήσεις πάνω σε τιμολόγια και αποδείξεις.

ΚΑΝΟΝΕΣ:
1. Απαντάς ΜΟΝΟ με βάση το CONTEXT που σου δίνεται.
2. Δεν χρησιμοποιείς εξωτερική γνώση.
3. Δεν μαντεύεις ποσά, ημερομηνίες, ονόματα, εταιρείες ή υπηρεσίες.
4. Αν η απάντηση δεν υπάρχει καθαρά στο CONTEXT, απαντάς ακριβώς:
"Δεν βρέθηκε στο έγγραφο."
5. Αν υπάρχει απάντηση, δώσε σύντομη απάντηση στα ελληνικά.
6. Πάντα να αναφέρεις:
- Πηγή αρχείου
- Σελίδα
- Απόσπασμα από το έγγραφο
"""


def build_context(chunks: List[Dict[str, Any]]) -> str:
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[CHUNK {i}]\n"
            f"Type: {chunk.get('type')}\n"
            f"Field name: {chunk.get('field_name')}\n"
            f"Line item index: {chunk.get('line_item_index')}\n"
            f"Value: {chunk.get('value')}\n"
            f"File: {chunk.get('filename')}\n"
            f"Page: {chunk.get('page')}\n"
            f"Source text: {chunk.get('source_text')}\n"
            f"Full text:\n{chunk.get('text')}\n"
        )

    return "\n---\n".join(context_parts)


def answer_question(question: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "Δεν βρέθηκε στο έγγραφο."

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in .env")

    client = genai.Client(api_key=api_key)
    context = build_context(chunks)

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUESTION:
{question}

Απάντησε με βάση ΜΟΝΟ το CONTEXT.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    return response.text or "Δεν βρέθηκε στο έγγραφο."