import streamlit as st
from PIL import Image
import io
import hashlib
from components.sidebar import render_sidebar
from components.chat import render_chat
from utils.api import ask_backend, upload_document

st.set_page_config(
    page_title="info4invo",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown,
    h1, h2, h3, h4, h5, h6, p, div, span, label, input, textarea, button {
        font-family: 'DM Sans', -apple-system, sans-serif !important;
    }

    :root {
        --green:       #1a7a4a;
        --green-mid:   #22a060;
        --green-light: #d6f5e6;
        --green-xl:    #f0faf5;
        --white:       #ffffff;
        --bg:          #f4f8f6;
        --border:      #d0e8da;
        --text:        #0f1f17;
        --muted:       #5a7a6a;
        --sidebar-bg:  #0b1e13;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, header, footer,
    .stDeployButton,
    [data-testid="stToolbar"],
    [data-testid="stSidebarHeader"] { display: none !important; }

    /* ── App & sidebar ── */
    .stApp { background: var(--bg) !important; }

    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid #152c1e !important;
    }
    [data-testid="stSidebar"] * { color: #b8d8c8 !important; }
    [data-testid="stSidebar"] hr { border-color: #162b1e !important; }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }

    /* ── Main block: no extra padding ── */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* ── Top bar ── */
    .topbar {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 13px 40px;
        background: var(--white);
        border-bottom: 1px solid var(--border);
    }
    .topbar-logo {
        width: 29px; height: 29px;
        background: var(--green);
        border-radius: 7px;
        display: flex; align-items: center; justify-content: center;
    }
    .topbar-name {
        font-size: 0.98rem; font-weight: 600;
        color: var(--text) !important; letter-spacing: -0.02em;
    }
    .topbar-badge {
        font-size: 0.68rem; font-weight: 500;
        background: var(--green-light); color: var(--green) !important;
        padding: 2px 7px; border-radius: 20px;
    }
    .topbar-right {
        margin-left: auto;
        font-size: 0.73rem; color: var(--muted) !important;
    }

    /* ── Center column ── */
    .center-col {
        max-width: 700px;
        margin: 0 auto;
        padding: 0 20px;
    }

    /* ── Welcome ── */
    .welcome-wrap {
        text-align: center;
        padding: 52px 0 36px 0;
    }
    .welcome-icon {
        width: 50px; height: 50px;
        background: var(--green-light);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 16px auto;
    }
    .welcome-title {
        font-size: 1.4rem; font-weight: 600;
        color: var(--text); letter-spacing: -0.03em; margin-bottom: 8px;
    }
    .welcome-sub {
        font-size: 0.86rem; color: var(--muted);
        max-width: 370px; margin: 0 auto 28px auto; line-height: 1.6;
    }
    .feat-row { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    .feat-card {
        background: var(--white); border: 1px solid var(--border);
        border-radius: 12px; padding: 14px 16px; width: 162px; text-align: left;
    }
    .feat-dot {
        width: 7px; height: 7px; background: var(--green);
        border-radius: 50%; margin-bottom: 8px;
    }
    .feat-label { font-size: 0.79rem; font-weight: 600; color: var(--text); margin-bottom: 3px; }
    .feat-desc  { font-size: 0.72rem; color: var(--muted); line-height: 1.4; }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        background: var(--white) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        margin-bottom: 8px !important;
        max-width: 700px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: var(--green-xl) !important;
        border-color: #b8e8cf !important;
    }
    [data-testid="stChatMessageContent"] p {
        color: var(--text) !important;
        font-size: 0.89rem !important;
        line-height: 1.65 !important;
        margin: 0 !important;
    }

    /* ── Chat input ── */
    [data-testid="stChatInputTextArea"] {
        background: var(--white) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 14px !important;
        color: var(--text) !important;
        font-size: 0.89rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stChatInputTextArea"]:focus {
        border-color: var(--green-mid) !important;
        box-shadow: 0 0 0 3px rgba(34,160,96,0.10) !important;
        outline: none !important;
    }
    [data-testid="stChatInputSubmitButton"] button {
        background: var(--green) !important;
        border-radius: 10px !important;
        border: none !important;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
        background: var(--green-mid) !important;
    }
    [data-testid="stChatInputSubmitButton"] svg { fill: white !important; }

    /* ── Bottom input container ── */
    .bottom-bar {
        max-width: 700px;
        margin: 0 auto;
        padding: 10px 20px 18px 20px;
        border-top: 1px solid var(--border);
        background: var(--bg);
    }

    /* ── Attach ── */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploader"] label { display: none !important; }

    .attach-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .attach-btn {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 5px 12px; border-radius: 20px;
        border: 1.5px solid var(--border); background: var(--white);
        color: var(--muted); font-size: 0.75rem; font-weight: 500;
        cursor: pointer; transition: border-color .15s, color .15s;
    }
    .attach-btn:hover { border-color: var(--green-mid); color: var(--green); }
    .file-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: var(--green-light); border: 1px solid #a8dfc0;
        border-radius: 20px; padding: 4px 10px;
        font-size: 0.73rem; color: var(--green); font-weight: 500;
        max-width: 200px; overflow: hidden;
        white-space: nowrap; text-overflow: ellipsis;
    }

    /* ── Confidence badges ── */
    .confidence-high {
        background:#e8f8ef; border-left:3px solid var(--green);
        padding:5px 10px; border-radius:6px; font-size:0.77rem; color:var(--green); margin:5px 0;
    }
    .confidence-medium {
        background:#fff8e6; border-left:3px solid #e6a817;
        padding:5px 10px; border-radius:6px; font-size:0.77rem; color:#a07010; margin:5px 0;
    }
    .confidence-low {
        background:#fef0f0; border-left:3px solid #e05252;
        padding:5px 10px; border-radius:6px; font-size:0.77rem; color:#c03030; margin:5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ──
for k, v in [
    ("messages", []), ("uploaded_files", {}),
    ("current_file_id", None), ("file_image", None),
    ("conversations", []), ("active_conversation", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ──
render_sidebar()

# ── Top bar ──
st.markdown("""
<div class="topbar">
  <div class="topbar-logo">
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
      <rect x="3" y="3" width="8" height="10" rx="1.5" fill="white" opacity=".9"/>
      <rect x="13" y="3" width="8" height="6" rx="1.5" fill="white" opacity=".6"/>
      <rect x="3" y="15" width="18" height="6" rx="1.5" fill="white" opacity=".75"/>
    </svg>
  </div>
  <span class="topbar-name">info4invo</span>
  <span class="topbar-badge">AI</span>
  <span class="topbar-right">Financial Document Assistant</span>
</div>
""", unsafe_allow_html=True)

# ── Main content ──
if st.session_state.current_file_id is None:
    st.markdown("""
<div class="center-col">
<div class="welcome-wrap">
  <div class="welcome-icon">
    <svg width="23" height="23" fill="none" viewBox="0 0 24 24">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
            stroke="#1a7a4a" stroke-width="1.8" stroke-linejoin="round"/>
      <polyline points="14 2 14 8 20 8" stroke="#1a7a4a" stroke-width="1.8" stroke-linejoin="round"/>
      <line x1="8" y1="13" x2="16" y2="13" stroke="#1a7a4a" stroke-width="1.8" stroke-linecap="round"/>
      <line x1="8" y1="17" x2="13" y2="17" stroke="#1a7a4a" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
  </div>
  <div class="welcome-title">Ask your financial documents</div>
  <div class="welcome-sub">Upload an invoice, receipt, or bank statement and ask anything — get verified answers with visual proof of the source.</div>
  <div class="feat-row">
    <div class="feat-card"><div class="feat-dot"></div><div class="feat-label">Accurate Answers</div><div class="feat-desc">Grounded responses cited to the source</div></div>
    <div class="feat-card"><div class="feat-dot"></div><div class="feat-label">Visual Proof</div><div class="feat-desc">See exactly where the answer comes from</div></div>
    <div class="feat-card"><div class="feat-dot"></div><div class="feat-label">Zero Hallucinations</div><div class="feat-desc">If it's not in the doc, we say so</div></div>
  </div>
</div>
</div>
""", unsafe_allow_html=True)
else:
    render_chat()

# ── Bottom input bar ──
# Divider line above
st.markdown('<hr style="margin:0;border:none;border-top:1px solid #d0e8da">', unsafe_allow_html=True)

# Attach row
col_attach, _ = st.columns([3, 7])
with col_attach:
    uploaded_file = st.file_uploader(
        "attach", type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed", key="main_uploader"
    )

fname_display = uploaded_file.name if uploaded_file else ""

if fname_display:
    st.markdown(f"""
<div style="max-width:700px;margin:6px auto 4px auto;padding:0 20px">
  <div class="attach-row">
    <button class="attach-btn" onclick="window.parent.document.querySelector('[data-testid=stFileUploader] input[type=file]').click()">
      <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Attach
    </button>
    <div class="file-pill">
      <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#1a7a4a" stroke-width="2" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="#1a7a4a" stroke-width="2"/></svg>
      {fname_display}
    </div>
  </div>
</div>""", unsafe_allow_html=True)
else:
    st.markdown("""
<div style="max-width:700px;margin:6px auto 4px auto;padding:0 20px">
  <button class="attach-btn" onclick="window.parent.document.querySelector('[data-testid=stFileUploader] input[type=file]').click()">
    <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Attach document
  </button>
</div>""", unsafe_allow_html=True)

# Process upload
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_key = hashlib.md5(file_bytes).hexdigest()
    if file_key not in st.session_state.uploaded_files:
        with st.spinner("Processing document..."):
            from utils.api import upload_document
            st.session_state.file_image = None
            result = upload_document(uploaded_file)
            st.session_state.uploaded_files[file_key] = {
                "file_id": result["file_id"],
                "filename": uploaded_file.name,
                "summary": result.get("summary", None)
            }
            st.session_state.current_file_id = result["file_id"]
            if uploaded_file.type.startswith("image"):
                st.session_state.file_image = Image.open(io.BytesIO(file_bytes))
            else:
                st.session_state.file_image = result.get("page_image", None)
            if st.session_state.messages:
                st.session_state.conversations.append({
                    "id": file_key,
                    "filename": uploaded_file.name,
                    "messages": list(st.session_state.messages),
                    "file_id": result["file_id"]
                })
            st.session_state.messages = []
        st.rerun()

# Chat input
if st.session_state.current_file_id:
    if prompt := st.chat_input("Ask anything about your document…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Analyzing..."):
            response = ask_backend(question=prompt, file_id=st.session_state.current_file_id)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["answer"],
            "confidence": response.get("confidence", 0),
            "evidence": response.get("evidence", None)
        })
        st.rerun()
else:
    st.chat_input("Attach a document to start chatting…", disabled=True)
