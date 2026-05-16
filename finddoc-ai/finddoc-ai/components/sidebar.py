import streamlit as st


def render_sidebar():
    """Render sidebar: branding, past conversations, example questions"""

    with st.sidebar:

        # ── Logo ──
        st.markdown("""
<div style="display:flex;align-items:center;gap:9px;padding:2px 0 2px 0">
  <div style="width:28px;height:28px;background:#22a060;border-radius:7px;
              display:flex;align-items:center;justify-content:center;flex-shrink:0">
    <svg width="15" height="15" fill="none" viewBox="0 0 24 24">
      <rect x="3" y="3" width="8" height="10" rx="1.5" fill="white" opacity=".9"/>
      <rect x="13" y="3" width="8" height="6" rx="1.5" fill="white" opacity=".6"/>
      <rect x="3" y="15" width="18" height="6" rx="1.5" fill="white" opacity=".75"/>
    </svg>
  </div>
  <div>
    <div style="font-size:0.92rem;font-weight:600;color:#e8f4ee;letter-spacing:-0.02em;line-height:1.1">info4invo</div>
    <div style="font-size:0.68rem;color:#4a7a5a;line-height:1.1">Financial AI Agent</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.divider()

        # ── New conversation button ──
        if st.button("+ New conversation", use_container_width=True):
            if st.session_state.messages:
                # Archive current conversation
                import hashlib, time
                conv_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
                fname = "Document"
                for data in st.session_state.get("uploaded_files", {}).values():
                    if data["file_id"] == st.session_state.get("current_file_id"):
                        fname = data["filename"]
                        break
                convs = st.session_state.get("conversations", [])
                convs.append({
                    "id": conv_id,
                    "filename": fname,
                    "messages": list(st.session_state.messages),
                    "file_id": st.session_state.get("current_file_id")
                })
                st.session_state.conversations = convs
            st.session_state.messages = []
            st.session_state.current_file_id = None
            st.session_state.file_image = None
            st.rerun()

        st.divider()

        # ── Past conversations ──
        conversations = st.session_state.get("conversations", [])

        st.markdown("""
<div style="font-size:0.7rem;font-weight:600;color:#4a6a58;
            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">
  Past Conversations
</div>""", unsafe_allow_html=True)

        if not conversations:
            st.markdown("""
<div style="font-size:0.78rem;color:#2e4d3c;padding:8px 0;font-style:italic">
  No previous conversations yet.
</div>""", unsafe_allow_html=True)
        else:
            # Show most recent first
            for conv in reversed(conversations):
                fname = conv.get("filename", "Document")
                n_msgs = len([m for m in conv.get("messages", []) if m["role"] == "user"])
                label = fname if len(fname) <= 26 else fname[:23] + "…"

                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"📄 {label}", key=f"conv_{conv['id']}", use_container_width=True):
                        # Restore conversation
                        st.session_state.messages = list(conv["messages"])
                        st.session_state.current_file_id = conv.get("file_id")
                        st.session_state.active_conversation = conv["id"]
                        st.rerun()
                with col2:
                    st.markdown(f"""<div style="font-size:0.68rem;color:#3a5a4a;
                        padding-top:8px;text-align:right">{n_msgs}q</div>""",
                        unsafe_allow_html=True)

        st.divider()

        # ── Current document info ──
        if st.session_state.get("current_file_id"):
            fname = None
            summary = None
            for data in st.session_state.get("uploaded_files", {}).values():
                if data["file_id"] == st.session_state.current_file_id:
                    fname = data["filename"]
                    summary = data.get("summary")
                    break

            st.markdown("""
<div style="font-size:0.7rem;font-weight:600;color:#4a6a58;
            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">
  Active Document
</div>""", unsafe_allow_html=True)

            if fname:
                st.markdown(f"""
<div style="background:#0d2a1a;border:1px solid #1a3d28;border-radius:9px;
            padding:9px 12px;font-size:0.8rem;color:#90c8a8;
            display:flex;align-items:center;gap:7px;margin-bottom:10px">
  <svg width="12" height="12" fill="none" viewBox="0 0 24 24">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
          stroke="#22a060" stroke-width="2" stroke-linejoin="round"/>
    <polyline points="14 2 14 8 20 8" stroke="#22a060" stroke-width="2"/>
  </svg>
  {fname[:28] + "…" if len(fname) > 28 else fname}
</div>""", unsafe_allow_html=True)

            if summary:
                st.markdown("""
<div style="font-size:0.7rem;font-weight:600;color:#4a6a58;
            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px">
  Summary
</div>""", unsafe_allow_html=True)
                rows = [
                    ("Vendor", summary.get("vendor", "—")),
                    ("Amount", summary.get("total", "—")),
                    ("Date",   summary.get("date", "—")),
                    ("Items",  summary.get("line_items_count", "—")),
                ]
                for label, val in rows:
                    st.markdown(f"""
<div style="display:flex;justify-content:space-between;padding:4px 0;
            border-bottom:1px solid #132510;font-size:0.78rem">
  <span style="color:#4a6a58">{label}</span>
  <span style="color:#a0c8b0;font-weight:500">{val}</span>
</div>""", unsafe_allow_html=True)

                if summary.get("alerts"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    for alert in summary["alerts"]:
                        st.warning(alert)

            st.divider()

        # ── Example questions ──
        st.markdown("""
<div style="font-size:0.7rem;font-weight:600;color:#4a6a58;
            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">
  Example Questions
</div>""", unsafe_allow_html=True)

        questions = [
            "Ποιο είναι το συνολικό ποσό;",
            "What's the vendor name?",
            "List all line items",
            "Ποια η ημερομηνία έκδοσης;",
            "Is there VAT included?",
        ]
        for q in questions:
            st.markdown(f"""
<div style="padding:6px 10px;border-radius:8px;font-size:0.77rem;
            color:#6a9a7a;border:1px solid #152510;margin-bottom:5px;
            background:#0a1e10;line-height:1.35">
  {q}
</div>""", unsafe_allow_html=True)

        # ── Footer ──
        st.markdown("""<br>""", unsafe_allow_html=True)
        st.markdown("""
<div style="font-size:0.68rem;color:#2e4d3c;line-height:1.8;border-top:1px solid #162b1e;padding-top:12px">
  Zero Hallucinations · Visual Evidence · AI-Powered
</div>""", unsafe_allow_html=True)
