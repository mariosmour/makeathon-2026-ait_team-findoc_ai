import uuid
from typing import Any, Dict, List


DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}


def build_chunks(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []
    filename = analysis["filename"]

    for field_name, data in analysis.get("fields", {}).items():
        value = data.get("value")
        content = data.get("content")

        if value is None and not content:
            continue

        text = (
            f"Document: {filename}\n"
            f"Field: {field_name}\n"
            f"Value: {value}\n"
            f"Source text: {content}\n"
        )

        chunks.append({
            "type": "field",
            "field_name": field_name,
            "text": text,
            "value": value,
            "source_text": content,
            "filename": filename,
            "page": data.get("page"),
            "polygon": data.get("polygon"),
            "confidence": data.get("confidence")
        })

    for idx, item in enumerate(analysis.get("line_items", []), start=1):
        parts = []
        source_parts = []

        for key, data in item.items():
            parts.append(f"{key}: {data.get('value')}")
            if data.get("content"):
                source_parts.append(data.get("content"))

        text = (
            f"Document: {filename}\n"
            f"Line item #{idx}\n"
            + "\n".join(parts)
            + "\n"
            f"Source text: {' | '.join(source_parts)}"
        )

        first_field = next(iter(item.values()), {})

        chunks.append({
            "type": "line_item",
            "line_item_index": idx,
            "text": text,
            "value": parts,
            "source_text": " | ".join(source_parts),
            "filename": filename,
            "page": first_field.get("page"),
            "polygon": first_field.get("polygon"),
            "confidence": first_field.get("confidence")
        })

    return chunks


def add_document(analysis: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(uuid.uuid4())
    chunks = build_chunks(analysis)

    DOCUMENT_STORE[doc_id] = {
        "doc_id": doc_id,
        "filename": analysis["filename"],
        "analysis": analysis,
        "chunks": chunks
    }

    return DOCUMENT_STORE[doc_id]


def simple_score(question: str, text: str, chunk: Dict[str, Any]) -> float:
    q = question.lower()

    field_name = str(chunk.get("field_name", "")).lower()
    chunk_type = str(chunk.get("type", "")).lower()
    chunk_text = text.lower()

    score = 0.0

    # Strong field-specific rules
    if any(word in q for word in ["invoice id", "invoice number", "αριθμός", "αριθμο", "id", "κωδικός", "κωδικο"]):
        if field_name in ["invoiceid", "invoicenumber"]:
            score += 10

    if any(word in q for word in [
        "date", "when", "issued", "issue", "receipt date", "invoice date",
        "ημερομηνία", "ημερομηνια", "πότε", "ποτε",
        "εκδόθηκε", "εκδοθηκε", "έκδοση", "εκδοση"
    ]):
        if field_name in [
            "invoicedate", "receiptdate", "transactiondate", "issuedate", "date"
        ]:
            score += 10

    if any(word in q for word in ["total", "amount", "σύνολο", "συνολο", "ποσό", "ποσο"]):
        if field_name in ["invoicetotal", "amountdue", "total"]:
            score += 10

    if any(word in q for word in ["vendor", "supplier", "προμηθευτής", "προμηθευτη"]):
        if field_name in ["vendorname", "suppliername"]:
            score += 10

    if any(word in q for word in ["customer", "client", "πελάτης", "πελατης"]):
        if field_name in ["customername"]:
            score += 10

    if any(word in q for word in ["due", "λήξη", "ληξη", "προθεσμία", "προθεσμια"]):
        if field_name in ["duedate"]:
            score += 10

    # Line item / description search
    if any(word in q for word in ["χρέωση", "χρεωση", "service", "υπηρεσία", "υπηρεσια", "item", "description", "περιγραφή", "περιγραφη"]):
        if chunk_type == "line_item":
            score += 3

    # Basic word overlap
    q_words = set(q.replace("?", "").replace(",", "").split())
    t_words = set(chunk_text.replace("?", "").replace(",", "").split())

    if q_words:
        overlap = q_words.intersection(t_words)
        score += len(overlap) / len(q_words)

    return score


def search_chunks(doc_id: str, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if doc_id not in DOCUMENT_STORE:
        raise ValueError("Document not found")

    scored_chunks = []

    for chunk in DOCUMENT_STORE[doc_id]["chunks"]:
        score = simple_score(question, chunk["text"], chunk)

        scored_chunks.append({
            **chunk,
            "score": score
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    return scored_chunks[:top_k]

def get_document(doc_id: str) -> Dict[str, Any]:
    if doc_id not in DOCUMENT_STORE:
        raise ValueError("Document not found"

        )

    return DOCUMENT_STORE[doc_id]