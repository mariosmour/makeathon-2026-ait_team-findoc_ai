from typing import Any, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.azure_invoice import analyze_invoice
from backend.rag import add_document, search_chunks, get_document
from backend.llm_agent import answer_question


app = FastAPI(
    title="FinDoc AI Backend",
    description="AI Agent for Q&A on invoices and receipts",
    version="0.1.0"
)

# Για να μπορεί να κουμπώσει μετά οποιοδήποτε frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    doc_id: str
    question: str


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "status": "ok",
        "message": "FinDoc AI backend is running"
    }


@app.post("/documents/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        file_bytes = await file.read()

        analysis = analyze_invoice(
            file_bytes=file_bytes,
            filename=file.filename
        )

        stored_doc = add_document(analysis)

        return {
            "doc_id": stored_doc["doc_id"],
            "filename": stored_doc["filename"],
            "fields": analysis["fields"],
            "line_items": analysis["line_items"],
            "chunk_count": len(stored_doc["chunks"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
async def ask_question(request: AskRequest) -> Dict[str, Any]:
    try:
        doc = get_document(request.doc_id)

        # Για το LLM δίνουμε ΟΛΑ τα chunks του συγκεκριμένου invoice.
        # Έτσι καταλαβαίνει καλύτερα συνώνυμα και δεν βασίζεται μόνο στο απλό search.
        all_chunks = doc["chunks"]

        # Για sources κρατάμε τα top chunks ώστε να μη γεμίζει το response.
        chunks = search_chunks(
            doc_id=request.doc_id,
            question=request.question,
            top_k=5
        )

        answer = answer_question(
            question=request.question,
            chunks=all_chunks
        )

        sources = [
            {
                "filename": chunk.get("filename"),
                "page": chunk.get("page"),
                "source_text": chunk.get("source_text") or str(chunk.get("value") or ""),
                "value": chunk.get("value"),
                "score": chunk.get("score"),
                "polygon": chunk.get("polygon"),
                "confidence": chunk.get("confidence")
            }
            for chunk in chunks
        ]

        return {
            "answer": answer,
            "sources": sources
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{doc_id}")
def read_document(doc_id: str) -> Dict[str, Any]:
    try:
        doc = get_document(doc_id)

        return {
            "doc_id": doc["doc_id"],
            "filename": doc["filename"],
            "fields": doc["analysis"]["fields"],
            "line_items": doc["analysis"]["line_items"],
            "chunk_count": len(doc["chunks"])
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/documents/extract-only")
async def extract_only(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        file_bytes = await file.read()

        analysis = analyze_invoice(
            file_bytes=file_bytes,
            filename=file.filename
        )

        return {
            "filename": analysis["filename"],
            "fields": analysis["fields"],
            "line_items": analysis["line_items"],
            "raw_text_preview": analysis["raw_text"][:1000]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))