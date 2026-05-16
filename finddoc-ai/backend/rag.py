import os
import uuid
from typing import Any, Dict, List
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Σύνδεση με Database (Supabase) ---
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key)

# --- Σύνδεση με OpenAI (για τα Vector Embeddings) ---
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def get_embedding(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


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

    # Insert document metadata into Supabase
    supabase.table("documents").insert({
        "doc_id": doc_id,
        "filename": analysis["filename"],
        "fields": analysis.get("fields", {}),
        "line_items": analysis.get("line_items", []),
        "raw_text": analysis.get("raw_text", "")
    }).execute()

    # Generate embeddings and insert chunks
    chunk_records = []
    for chunk in chunks:
        emb = get_embedding(chunk["text"])
        chunk_records.append({
            "doc_id": doc_id,
            "filename": chunk.get("filename"),
            "page": chunk.get("page"),
            "source_text": chunk.get("text"),
            "polygon": chunk.get("polygon"),
            "embedding": emb
        })

    if chunk_records:
        supabase.table("document_chunks").insert(chunk_records).execute()

    return {
        "doc_id": doc_id,
        "filename": analysis["filename"],
        "chunks": chunks
    }


def search_chunks(doc_id: str, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_embedding = get_embedding(question)

    response = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_threshold": 0.2,
        "match_count": top_k,
        "p_doc_id": doc_id
    }).execute()

    results = []
    for row in response.data:
        results.append({
            "filename": row.get("filename"),
            "page": row.get("page"),
            "source_text": row.get("source_text"),
            "polygon": row.get("polygon"),
            "score": row.get("similarity", 0) * 10
        })

    return results


def get_document(doc_id: str) -> Dict[str, Any]:
    doc_res = supabase.table("documents").select(
        "*").eq("doc_id", doc_id).execute()
    if not doc_res.data:
        raise ValueError("Document not found")

    doc_data = doc_res.data[0]
    chunks_res = supabase.table("document_chunks").select(
        "*").eq("doc_id", doc_id).execute()

    return {
        "doc_id": doc_id,
        "filename": doc_data["filename"],
        "analysis": {
            "fields": doc_data.get("fields"),
            "line_items": doc_data.get("line_items")
        },
        "chunks": chunks_res.data
    }
