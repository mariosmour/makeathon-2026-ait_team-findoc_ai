import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

load_dotenv()


SYSTEM_PROMPT = """
You are an AI assistant for invoices and receipts.

RULES:
1. Answer ONLY using the provided CONTEXT.
2. Do not use outside knowledge.
3. Do not guess amounts, dates, names, vendors, customers, taxes, or services.
4. If the answer is not clearly present in the CONTEXT, answer:
   "Δεν βρέθηκε στο έγγραφο." if the user asks in Greek,
   or "Not found in the document." if the user asks in English.
5. If the answer exists, answer briefly and clearly.
6. Answer in the same language as the user's question.
7. For total amount questions, look for fields like InvoiceTotal, AmountDue, Total, or receipt total.
8. For vendor/supplier questions, look for VendorName or SupplierName.
9. For date questions, look for InvoiceDate, ReceiptDate, TransactionDate, or IssueDate.
10. For line item questions, use the line item chunks.
11. Do not mention information that is not in the context.
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

Answer using ONLY the CONTEXT. Use the same language as the user's question.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    return response.text or "Δεν βρέθηκε στο έγγραφο."