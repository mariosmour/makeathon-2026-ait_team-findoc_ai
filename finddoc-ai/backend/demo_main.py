"""
FinDoc AI — Simple Demo Backend (χωρίς LLM)
Απλά επιστρέφει mock data για να δεις το frontend οπτικά.
"""

import uuid
import base64
import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

# ── Setup ─────────────────────────────────────────────────
app = FastAPI(title="FinDoc AI - Demo Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Αποθήκη για τα uploaded αρχεία
document_store: dict = {}


# ── Helpers ───────────────────────────────────────────────

def image_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Endpoints ─────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "mode": "demo"}


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_id = str(uuid.uuid4())

    # Φόρτωσε την εικόνα
    try:
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        page_image_b64 = image_to_b64(image)
    except Exception:
        page_image_b64 = None

    # Αποθήκευσε
    document_store[file_id] = {
        "filename": file.filename,
        "image_bytes": file_bytes,
    }

    # Mock summary
    return {
        "file_id": file_id,
        "summary": {
            "vendor": "TechCorp Solutions Ltd",
            "total": "€1.450,00",
            "date": "12/03/2026",
            "line_items_count": 4,
            "alerts": ["⚠️ Cloud Hosting cost +32% vs previous invoice"]
        },
        "page_image_b64": page_image_b64,
    }


class AskRequest(BaseModel):
    question: str
    file_id: str


@app.post("/api/ask")
async def ask_question(req: AskRequest):
    if req.file_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found.")

    q = req.question.lower()

    if any(w in q for w in ["ποσό", "total", "amount", "σύνολο"]):
        return {
            "answer": "Το συνολικό ποσό είναι **€1.450,00** (συμπ. ΦΠΑ 24%: €280,65).",
            "confidence": 0.94,
            "evidence": {
                "text": "€1.450,00",
                "bbox": {"x": 380, "y": 520, "w": 120, "h": 28},
                "page": 1
            }
        }
    elif any(w in q for w in ["vendor", "εταιρεία", "προμηθευτ", "company"]):
        return {
            "answer": "Ο προμηθευτής είναι η **TechCorp Solutions Ltd**.",
            "confidence": 0.97,
            "evidence": {
                "text": "TechCorp Solutions Ltd",
                "bbox": {"x": 50, "y": 80, "w": 200, "h": 25},
                "page": 1
            }
        }
    elif any(w in q for w in ["date", "ημερομηνία", "πότε"]):
        return {
            "answer": "Η ημερομηνία έκδοσης είναι **12/03/2026**.",
            "confidence": 0.96,
            "evidence": {
                "text": "12/03/2026",
                "bbox": {"x": 420, "y": 150, "w": 100, "h": 20},
                "page": 1
            }
        }
    elif any(w in q for w in ["items", "γραμμ", "line", "προϊόν"]):
        return {
            "answer": (
                "Τα line items είναι:\n\n"
                "| # | Περιγραφή | Ποσό |\n"
                "|---|-----------|------|\n"
                "| 1 | Cloud Hosting | €650,00 |\n"
                "| 2 | API Calls | €350,00 |\n"
                "| 3 | Support License | €250,00 |\n"
                "| 4 | Data Backup | €200,00 |"
            ),
            "confidence": 0.91,
            "evidence": {
                "text": "Line Items Table",
                "bbox": {"x": 40, "y": 250, "w": 500, "h": 180},
                "page": 1
            }
        }
    else:
        return {
            "answer": "🤔 Δεν βρέθηκε αυτή η πληροφορία στο έγγραφο. Δοκίμασε: ποσό, ημερομηνία, vendor, line items.",
            "confidence": 0.0,
            "evidence": None
        }


@app.get("/api/summary/{file_id}")
def get_summary(file_id: str):
    if file_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "vendor": "TechCorp Solutions Ltd",
        "total": "€1.450,00",
        "date": "12/03/2026",
        "line_items_count": 4,
        "alerts": ["⚠️ Cloud Hosting cost +32% vs previous invoice"]
    }
