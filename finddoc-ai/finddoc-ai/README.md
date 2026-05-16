# 🧾 FinDoc AI — Intelligent Financial Document Assistant

> AI-powered agent that extracts, understands, and answers questions about financial documents with **visual evidence** and **zero hallucinations**.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)
![Pillow](https://img.shields.io/badge/Pillow-10.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🏦 About

**FinDoc AI** is a RAG-based AI agent developed for the **INFORM × UniAI Makeathon 2026**. It processes invoices, receipts, and financial documents — answering user questions based strictly on document content, while providing visual proof (bounding-box highlights) of exactly where each answer was found.

Supports both **Greek and English** queries out of the box.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Accurate Q&A** | Grounded answers strictly from document content |
| 🖼️ **Visual Evidence** | Highlighted bounding boxes showing the exact source location |
| 🛡️ **Zero Hallucinations** | If it's not in the document, the system says so |
| 📊 **Auto-Summary** | Instant vendor, amount, date & line-item analysis on upload |
| ⚠️ **Smart Alerts** | Detects anomalies and flags issues (e.g. price spikes) |
| 🟢 **Confidence Scores** | Color-coded confidence badge per answer (High / Medium / Low) |
| 💬 **Multi-turn Chat** | Conversation memory for follow-up questions |
| 🌐 **Bilingual** | Supports Greek (ελληνικά) and English queries |

---

## 📁 Project Structure

```
FinDocAI/
├── app.py                  # Main Streamlit entry point
├── requirements.txt        # Python dependencies
├── components/
│   ├── __init__.py
│   ├── chat.py             # Chat history rendering + confidence badges
│   ├── sidebar.py          # File upload, document preview, auto-summary
│   └── evidence.py         # Bounding box highlighting + zoomed crop view
├── utils/
│   ├── __init__.py
│   └── api.py              # Backend API calls + demo mock mode
└── .streamlit/
    └── config.toml         # Theme and server configuration
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/findoc-ai.git
cd findoc-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure backend URL (optional)

Create a `.streamlit/secrets.toml` file:

```toml
BACKEND_URL = "http://your-backend-url:8000"
```

If no backend is configured, the app runs in **Demo Mode** with mock data automatically.

### 4. Run the app

```bash
streamlit run app.py
```

---

## 🖥️ Usage

1. **Upload** an invoice, receipt, or bank statement (PDF, PNG, JPG) via the sidebar
2. View the **Auto-Summary** — vendor, total amount, date, and line items are extracted instantly
3. **Ask questions** in Greek or English in the chat input
4. See the answer with a **confidence score** and **visual evidence** highlighting exactly where it was found in the document

### Example Questions

```
Ποιο είναι το συνολικό ποσό;
What's the vendor name?
List all line items
Ποια η ημερομηνία έκδοσης;
Is there VAT included?
```

---

## 🔌 Backend API Contract

The frontend expects a backend with the following endpoints:

### `POST /api/upload`
Accepts a multipart file upload.

**Response:**
```json
{
  "file_id": "abc123",
  "summary": {
    "vendor": "TechCorp Solutions Ltd",
    "total": "€1.450,00",
    "date": "12/03/2026",
    "line_items_count": 4,
    "alerts": ["Cloud Hosting cost +32% vs previous invoice"]
  },
  "page_image_b64": "<base64-encoded PNG of first page>"
}
```

### `POST /api/ask`
**Request:**
```json
{
  "question": "What is the total amount?",
  "file_id": "abc123"
}
```

**Response:**
```json
{
  "answer": "The total amount is €1.450,00",
  "confidence": 0.94,
  "evidence": {
    "text": "€1.450,00",
    "bbox": {"x": 380, "y": 520, "w": 120, "h": 28},
    "page": 1
  }
}
```

---

## 🧪 Demo Mode

If no backend is running, the app automatically falls back to **Demo Mode** with realistic mock data. This allows full frontend testing without a backend.

Mock responses are defined in `utils/api.py` inside `_mock_upload()` and `_mock_answer()`.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Image Processing:** Pillow (PIL) — bounding box highlighting, crop, RGBA compositing
- **HTTP Client:** Requests
- **Backend:** Pluggable (FastAPI recommended) — see API contract above

---

## 📄 License

MIT License — built for the INFORM × UniAI Makeathon 2026.
