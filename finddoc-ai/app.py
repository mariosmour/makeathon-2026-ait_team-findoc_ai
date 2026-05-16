
import streamlit as st
from PIL import Image
import io
from components.sidebar import render_sidebar
from components.chat import render_chat
from components.evidence import render_evidence_display
from utils.api import ask_backend

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="FinDoc AI | Smart Document Assistant",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    /* Confidence badges */
    .confidence-high {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 4px 0;
    }
    .confidence-medium {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 4px 0;
    }
    .confidence-low {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 4px 0;
    }

    /* Evidence card */
    .evidence-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        background-color: #f8f9fa;
        margin-top: 8px;
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }

    /* Upload success */
    .upload-success {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ===== SESSION STATE INIT =====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None
if "file_image" not in st.session_state:
    st.session_state.file_image = None

# ===== SIDEBAR =====
render_sidebar()

# ===== MAIN AREA =====
st.markdown("## 🧾 FinDoc AI")
st.markdown(
    "*Intelligent Financial Document Assistant — Ask anything, get verified answers*")
st.divider()

# Check if file is uploaded
if st.session_state.current_file_id is None:
    # Welcome screen
    st.markdown("### 👋 Welcome!")
    st.info(
        "📁 **Upload a financial document** (invoice, receipt, bank statement) "
        "from the sidebar to get started."
        "Then ask me anything about it — I'll answer with visual proof!"
    )

    # Demo features
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🎯 Accurate Answers")
        st.markdown("Grounded responses with source citations")
    with col2:
        st.markdown("#### 🖼️ Visual Proof")
        st.markdown("See exactly where the answer comes from")
    with col3:
        st.markdown("#### 🛡️ Zero Hallucinations")
        st.markdown("If it's not in the document, we say so")

else:
    # Chat interface
    render_chat()

    # Chat input
    if prompt := st.chat_input("π.χ. Ποιο είναι το συνολικό ποσό; / What's the total amount?"):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Get response from backend
        with st.spinner("🔍 Analyzing document..."):
            response = ask_backend(
                question=prompt,
                file_id=st.session_state.current_file_id
            )

        # Add assistant message with evidence
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["answer"],
            "confidence": response.get("confidence", 0),
            "evidence": response.get("evidence", None)
        })

        st.rerun()
