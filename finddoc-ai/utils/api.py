
import streamlit as st
import requests
from PIL import Image
import io
import base64

# ===== CONFIGURATION =====
# Change this to your backend URL
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")


def upload_document(uploaded_file) -> dict:
    """
    Upload a document to the backend for processing.

    Returns:
        {
            "file_id": "abc123",
            "summary": {
                "vendor": "TechCorp",
                "total": "€1.450,00",
                "date": "12/03/2026",
                "line_items_count": 4,
                "alerts": ["Price increased 32% vs last invoice"]
            },
            "page_image": PIL.Image (first page rendered as image)
        }
    """
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        response = requests.post(
            f"{BACKEND_URL}/api/upload",
            files=files,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # If backend returns page image as base64, convert to PIL
        if data.get("page_image_b64"):
            img_bytes = base64.b64decode(data["page_image_b64"])
            data["page_image"] = Image.open(io.BytesIO(img_bytes))

        return data

    except requests.exceptions.ConnectionError:
        # DEMO MODE: Return mock data when backend is not available
        return _mock_upload(uploaded_file)

    except Exception as e:
        st.error(f"Upload error: {e}")
        return _mock_upload(uploaded_file)


def ask_backend(question: str, file_id: str) -> dict:
    """
    Send a question to the backend and get an answer with evidence.

    Returns:
        {
            "answer": "The total amount is €1.450,00",
            "confidence": 0.94,
            "evidence": {
                "text": "€1.450,00",
                "bbox": {"x": 420, "y": 315, "w": 95, "h": 22},
                "page": 1
            },
            "source_file": "invoice_03.pdf"
        }
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/ask",
            json={
                "question": question,
                "file_id": file_id
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        # DEMO MODE
        return _mock_answer(question)

    except Exception as e:
        return {
            "answer": f"⚠️ Error communicating with backend: {str(e)}",
            "confidence": 0,
            "evidence": None
        }


def get_auto_summary(file_id: str) -> dict:
    """Get auto-generated summary for an uploaded document"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/summary/{file_id}",
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


# ===== DEMO/MOCK DATA =====
# Remove these functions when backend is ready!

def _mock_upload(uploaded_file) -> dict:
    """Mock upload response for frontend development"""
    return {
        "file_id": "demo_001",
        "summary": {
            "vendor": "TechCorp Solutions Ltd",
            "total": "€1.450,00",
            "date": "12/03/2026",
            "line_items_count": 4,
            "alerts": [
                "⚠️ Cloud Hosting cost +32% vs previous invoice"
            ]
        },
        "page_image": None
    }


def _mock_answer(question: str) -> dict:
    """Mock answer for frontend development/demo"""
    question_lower = question.lower()

    # Simulate different answers based on question
    if any(word in question_lower for word in ["ποσό", "total", "amount", "σύνολο"]):
        return {
            "answer": "Το συνολικό ποσό του τιμολογίου είναι **€1.450,00** (συμπ. ΦΠΑ 24%: €280,65).",
            "confidence": 0.94,
            "evidence": {
                "text": "€1.450,00",
                "bbox": {"x": 380, "y": 520, "w": 120, "h": 28},
                "page": 1
            }
        }
    elif any(word in question_lower for word in ["vendor", "εταιρεία", "προμηθευτ", "company"]):
        return {
            "answer": "Ο προμηθευτής είναι η **TechCorp Solutions Ltd**, με ΑΦΜ: EL123456789.",
            "confidence": 0.97,
            "evidence": {
                "text": "TechCorp Solutions Ltd",
                "bbox": {"x": 50, "y": 80, "w": 200, "h": 25},
                "page": 1
            }
        }
    elif any(word in question_lower for word in ["date", "ημερομηνία", "πότε", "when"]):
        return {
            "answer": "Η ημερομηνία έκδοσης είναι **12/03/2026**.",
            "confidence": 0.96,
            "evidence": {
                "text": "12/03/2026",
                "bbox": {"x": 420, "y": 150, "w": 100, "h": 20},
                "page": 1
            }
        }
    elif any(word in question_lower for word in ["items", "γραμμ", "προϊόντ", "line"]):
        return {
            "answer": "Τα line items του τιμολογίου είναι:"
                      "| # | Περιγραφή | Ποσό |"
                      "|---|-----------|------|"
                      "| 1 | Cloud Hosting (Monthly) | €650,00 |"
                      "| 2 | API Calls Package | €350,00 |"
                      "| 3 | Support License | €250,00 |"
                      "| 4 | Data Backup Service | €200,00 |",
            "confidence": 0.91,
            "evidence": {
                "text": "Line Items Table",
                "bbox": {"x": 40, "y": 250, "w": 500, "h": 180},
                "page": 1
            }
        }
    else:
        # Out-of-scope / unknown
        return {
            "answer": "🤔 Δεν μπόρεσα να βρω αυτή την πληροφορία στο έγγραφο. "
                      "Μπορείτε να ρωτήσετε για: ποσά, ημερομηνίες, vendor, line items.",
            "confidence": 0.0,
            "evidence": None
        }
