import io
import uuid
import base64
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import requests # Χρειάζεται για την κλήση στο API της ΑΑΔΕ

# --- Mock Document Store ---
document_store = {}

app = FastAPI(title="FinDoc AI - Demo Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def image_to_b64(image: Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --- ΑΑΔΕ & myDATA Mock Integration ---
def validate_with_aade(afm: str, extracted_name: str, extracted_amount: str) -> dict:
    """
    Mock συνάρτηση που προσομοιώνει την κλήση στο API της ΑΑΔΕ και του myDATA.
    Σε ένα πραγματικό σενάριο, εδώ θα γινόταν το HTTP Request προς την ΑΑΔΕ.
    """
    # Προσομοίωση αποτελέσματος από ΑΑΔΕ (Μητρώο)
    aade_status = "ACTIVE"
    aade_official_name = "TechCorp Solutions Ltd" # Προσομοίωση ταύτισης

    # Προσομοίωση αποτελέσματος από myDATA
    mydata_status = "MATCH" # Υποθέτουμε ότι το ποσό βρέθηκε
    mark_id = "4000001234567"

    validation_result = {
        "aade_check": "ΕΠΙΤΥΧΗΣ" if aade_status == "ACTIVE" else "ΑΠΟΤΥΧΗΜΕΝΟΣ",
        "mydata_check": "ΔΙΑΣΤΑΥΡΩΘΗΚΕ" if mydata_status == "MATCH" else "ΕΚΚΡΕΜΕΙ",
        "aade_name": aade_official_name,
        "mark": mark_id if mydata_status == "MATCH" else None,
        "details": ""
    }

    if validation_result["aade_check"] == "ΕΠΙΤΥΧΗΣ" and validation_result["mydata_check"] == "ΔΙΑΣΤΑΥΡΩΘΗΚΕ":
        validation_result["details"] = f"Το ΑΦΜ ({afm}) είναι ενεργό. Η ονομασία ('{extracted_name}') ταιριάζει με τα στοιχεία της ΑΑΔΕ. Το παραστατικό διασταυρώθηκε στο myDATA (MARK: {mark_id})."
    else:
         validation_result["details"] = "Προσοχή: Υπάρχει ασυμφωνία στα στοιχεία της ΑΑΔΕ ή το παραστατικό δεν έχει διαβιβαστεί στο myDATA."
    
    return validation_result

# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo"}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        page_image_b64 = image_to_b64(image)
        file_id = str(uuid.uuid4())

        # Mock OCR Extraction Data (Προσαρμοσμένα για TechCorp)
        extracted_text = "Τιμολόγιο από TechCorp Solutions Ltd με ΑΦΜ 094123456. Συνολικό ποσό: €1.450,00"
        vendor_name = "TechCorp Solutions Ltd"
        total_amount = "€1.450,00"

        # Εξαγωγή ΑΦΜ με Regex (υποθέτουμε 9 ψηφία)
        afm_pattern = re.compile(r'\b\d{9}\b')
        extracted_afms = afm_pattern.findall(extracted_text)
        afm_to_check = extracted_afms[0] if extracted_afms else None

        # Κλήση στην ΑΑΔΕ (Mock)
        aade_info = None
        if afm_to_check:
             aade_info = validate_with_aade(afm_to_check, vendor_name, total_amount)
        else:
             aade_info = {"aade_check": "ΣΦΑΛΜΑ", "details": "Δεν εντοπίστηκε ΑΦΜ στο έγγραφο."}

        # Αποθήκευση στο store με τα νέα πεδία της ΑΑΔΕ
        document_store[file_id] = {
            "filename": file.filename,
            "image_bytes": file_bytes,
            "file_id": file_id,
            "summary": {
                "vendor": vendor_name,
                "total": total_amount,
                "date": "12/03/2026",
                "line_items_count": 4,
                "alerts": "⚠️ Cloud Hosting cost +32% vs previous invoice",
                "aade_validation": aade_info # Προσθήκη των στοιχείων ΑΑΔΕ
            },
            "page_image_b64": page_image_b64,
            "raw_text": extracted_text # Αποθηκεύουμε και το raw text για μελλοντική χρήση
        }

        return {
            "file_id": file_id,
            "filename": file.filename,
            "summary": document_store[file_id]["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AskRequest(BaseModel):
    file_id: str
    question: str

@app.post("/api/ask")
def ask_question(req: AskRequest):
    if req.file_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    doc_data = document_store[req.file_id]
    q_lower = req.question.lower()
    aade_context = doc_data["summary"].get("aade_validation", {})

    # Εμπλουτισμός του Q&A με απαντήσεις σχετικά με την ΑΑΔΕ/myDATA
    if any(keyword in q_lower for keyword in ["ααδε", "aade", "mydata", "έγκυρο", "εγκυρότητα", "μητρώο"]):
        return {
            "answer": aade_context.get("details", "Δεν υπάρχουν διαθέσιμα στοιχεία επαλήθευσης ΑΑΔΕ."),
            "confidence": 0.95,
            "evidence": {
                "text": f"Στοιχεία myDATA: {aade_context.get('mark', 'N/A')}",
                "bbox": {"x": 50, "y": 50, "w": 200, "h": 30},
                "page": 1
            }
        }
    
    # ... (Υπόλοιπη λογική του ask_question όπως ήταν στο αρχικό αρχείο)
    elif any(keyword in q_lower for keyword in ["ποσό", "σύνολο", "amount", "total"]):
         return {
            "answer": "Το συνολικό ποσό είναι **€1.450,00** (συμπ. ΦΠΑ 24%: €280,65).",
            "confidence": 0.98,
            "evidence": {
                "text": "€1.450,00",
                "bbox": {"x": 500, "y": 800, "w": 100, "h": 30},
                "page": 1
            }
        }
    elif any(keyword in q_lower for keyword in ["εταιρεία", "προμηθευτής", "company", "vendor"]):
         return {
             "answer": "Ο προμηθευτής είναι η **TechCorp Solutions Ltd**.",
             "confidence": 0.99,
             "evidence": {
                 "text": "TechCorp Solutions Ltd",
                 "bbox": {"x": 100, "y": 100, "w": 250, "h": 40},
                 "page": 1
             }
         }
    elif any(keyword in q_lower for keyword in ["ημερομηνία", "πότε", "date"]):
        return {
             "answer": "Η ημερομηνία έκδοσης είναι **12/03/2026**.",
             "confidence": 0.97,
             "evidence": {
                 "text": "12/03/2026",
                 "bbox": {"x": 450, "y": 150, "w": 120, "h": 30},
                 "page": 1
             }
         }
    elif any(keyword in q_lower for keyword in ["items", "γραμμές", "προϊόντα"]):
        return {
            "answer": "Τα line items είναι:\n\n| # | Περιγραφή | Ποσό |\n|---|-----------|------|\n| 1 | Cloud Hosting | €650,00 |\n| 2 | API Calls | €350,00 |\n| 3 | Support License | €250,00 |\n| 4 | Data Backup | €200,00 |",
            "confidence": 0.95,
            "evidence": {
                 "text": "Line Items Table",
                 "bbox": {"x": 50, "y": 300, "w": 500, "h": 200},
                 "page": 1
             }
        }
    else:
        return {
            "answer": "🤔 Δεν βρήκα αυτή τη πληροφορία στο έγγραφο. Δοκιμάστε: ποσό, ημερομηνία, vendor, line items, ή έλεγχος myDATA.",
            "confidence": 0.0,
            "evidence": None
        }

@app.get("/api/summary/{file_id}")
def get_summary(file_id: str):
    if file_id not in document_store:
         raise HTTPException(status_code=404, detail="Document not found.")
    
    return document_store[file_id]["summary"]