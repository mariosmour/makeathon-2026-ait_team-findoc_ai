import streamlit as st
import requests
from PIL import Image
import io
import base64

# ===== CONFIGURATION =====
BACKEND_URL = st.secrets["BACKEND_URL"] if "BACKEND_URL" in st.secrets else "http://localhost:8000"


# ===== HELPERS =====

def polygon_to_bbox(polygon: list, img_w: int, img_h: int) -> dict:
    """
    Convert Azure polygon (normalized 0-1 coordinates) to pixel bbox.
    Azure polygon format: [x1,y1, x2,y2, x3,y3, x4,y4]
    """
    if not polygon or len(polygon) < 4:
        return None
    try:
        xs = [polygon[i] * img_w for i in range(0, len(polygon), 2)]
        ys = [polygon[i] * img_h for i in range(1, len(polygon), 2)]
        x = int(min(xs))
        y = int(min(ys))
        w = int(max(xs) - min(xs))
        h = int(max(ys) - min(ys))
        return {"x": x, "y": y, "w": w, "h": h}
    except Exception:
        return None


def build_summary_from_fields(fields: dict, line_items: list) -> dict:
    """
    Build the summary dict the frontend expects
    from the Azure Document Intelligence fields.
    """
    def get_val(key):
        f = fields.get(key, {})
        return f.get("value") if f else None

    vendor = get_val("VendorName") or get_val("SupplierName") or "N/A"
    total = get_val("InvoiceTotal") or get_val("AmountDue") or get_val("Total") or "N/A"
    date = get_val("InvoiceDate") or "N/A"
    count = len(line_items) if line_items else 0

    alerts = []
    tax = get_val("TotalTax")
    if tax and total and total != "N/A":
        try:
            tax_val = float(str(tax).replace(",", ".").replace("€", "").split()[0])
            total_val = float(str(total).replace(",", ".").replace("€", "").split()[0])
            if total_val > 0:
                tax_rate = tax_val / total_val
                if tax_rate > 0.30:
                    alerts.append(f"⚠️ ΦΠΑ φαίνεται υψηλό ({tax_rate:.0%})")
        except Exception:
            pass

    due_date = get_val("DueDate")
    if due_date:
        alerts.append(f"📅 Προθεσμία πληρωμής: {due_date}")

    return {
        "vendor": vendor,
        "total": total,
        "date": date,
        "line_items_count": count,
        "alerts": alerts
    }


# ===== MAIN FUNCTIONS =====

def upload_document(uploaded_file) -> dict:
    """
    Upload document to backend → POST /documents/analyze
    Returns format that frontend expects.
    """
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(
            f"{BACKEND_URL}/documents/analyze",
            files=files,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        summary = build_summary_from_fields(
            data.get("fields", {}),
            data.get("line_items", [])
        )

        page_image = None
        if uploaded_file.type.startswith("image"):
            page_image = Image.open(io.BytesIO(uploaded_file.getvalue()))

        return {
            "file_id": data["doc_id"],
            "summary": summary,
            "page_image": page_image,
            "fields": data.get("fields", {}),
            "line_items": data.get("line_items", [])
        }

    except requests.exceptions.ConnectionError:
        return _mock_upload(uploaded_file)
    except Exception as e:
        st.error(f"Upload error: {e}")
        return _mock_upload(uploaded_file)


def ask_backend(question: str, file_id: str) -> dict:
    """
    Ask a question → POST /ask
    Converts backend response to frontend format.
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask",
            json={
                "doc_id": file_id,
                "question": question
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "Δεν βρέθηκε απάντηση.")
        sources = data.get("sources", [])

        evidence = None
        confidence = 0.7

        if sources:
            best = sources[0]
            score = best.get("score", 0)
            confidence = min(score / 10.0, 1.0) if score else 0.7

            polygon = best.get("polygon")
            img = st.session_state.get("file_image")
            bbox = None

            if polygon and img:
                bbox = polygon_to_bbox(polygon, img.width, img.height)

            evidence = {
                "text": best.get("source_text", ""),
                "bbox": bbox,
                "page": best.get("page", 1)
            }

        return {
            "answer": answer,
            "confidence": confidence,
            "evidence": evidence
        }

    except requests.exceptions.ConnectionError:
        return _mock_answer(question)
    except Exception as e:
        return {
            "answer": f"⚠️ Σφάλμα επικοινωνίας με το backend: {str(e)}",
            "confidence": 0,
            "evidence": None
        }


def get_auto_summary(file_id: str) -> dict:
    """GET /documents/{doc_id}"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/documents/{file_id}",
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return build_summary_from_fields(
            data.get("fields", {}),
            data.get("line_items", [])
        )
    except Exception:
        return None


# ===== DEMO/MOCK DATA =====

def _mock_upload(uploaded_file) -> dict:
    page_image = None
    if uploaded_file.type.startswith("image"):
        page_image = Image.open(io.BytesIO(uploaded_file.getvalue()))
    return {
        "file_id": "demo_001",
        "summary": {
            "vendor": "TechCorp Solutions Ltd",
            "total": "€1.450,00",
            "date": "12/03/2026",
            "line_items_count": 4,
            "alerts": ["⚠️ Cloud Hosting cost +32% vs previous invoice"]
        },
        "page_image": page_image
    }


def _mock_answer(question: str) -> dict:
    q = question.lower()
    if any(w in q for w in ["ποσό", "total", "amount", "σύνολο"]):
        return {
            "answer": "Το συνολικό ποσό του τιμολογίου είναι **€1.450,00** (συμπ. ΦΠΑ 24%: €280,65).",
            "confidence": 0.94,
            "evidence": {"text": "€1.450,00", "bbox": {"x": 380, "y": 520, "w": 120, "h": 28}, "page": 1}
        }
    elif any(w in q for w in ["vendor", "εταιρεία", "προμηθευτ", "company"]):
        return {
            "answer": "Ο προμηθευτής είναι η **TechCorp Solutions Ltd**.",
            "confidence": 0.97,
            "evidence": {"text": "TechCorp Solutions Ltd", "bbox": {"x": 50, "y": 80, "w": 200, "h": 25}, "page": 1}
        }
    elif any(w in q for w in ["date", "ημερομηνία", "πότε", "when"]):
        return {
            "answer": "Η ημερομηνία έκδοσης είναι **12/03/2026**.",
            "confidence": 0.96,
            "evidence": {"text": "12/03/2026", "bbox": {"x": 420, "y": 150, "w": 100, "h": 20}, "page": 1}
        }
    elif any(w in q for w in ["items", "γραμμ", "προϊόντ", "line", "τιμολόγ"]):
        return {
            "answer": (
                "Τα line items:\n\n"
                "| # | Περιγραφή | Ποσό |\n|---|-----------|------|\n"
                "| 1 | Cloud Hosting | €650,00 |\n"
                "| 2 | API Calls | €350,00 |\n"
                "| 3 | Support License | €250,00 |\n"
                "| 4 | Data Backup | €200,00 |"
            ),
            "confidence": 0.91,
            "evidence": {"text": "Line Items", "bbox": {"x": 40, "y": 250, "w": 500, "h": 180}, "page": 1}
        }
    else:
        return {
            "answer": "🤔 Δεν βρέθηκε αυτή η πληροφορία στο έγγραφο.",
            "confidence": 0.0,
            "evidence": None
        }
