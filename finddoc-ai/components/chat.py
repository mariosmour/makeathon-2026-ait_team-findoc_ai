
import streamlit as st
from components.evidence import render_evidence_display


def get_confidence_html(confidence: float) -> str:
    """Return styled confidence badge"""
    if confidence >= 0.85:
        return f'<div class="confidence-high">🟢 High Confidence ({confidence:.0%})</div>'
    elif confidence >= 0.60:
        return f'<div class="confidence-medium">🟡 Medium Confidence ({confidence:.0%})</div>'
    else:
        return f'<div class="confidence-low">🔴 Low Confidence ({confidence:.0%}) — verify manually</div>'


def render_chat():
    """Render the full chat history with evidence"""

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Message text
            st.markdown(msg["content"])

            # If assistant message, show extras
            if msg["role"] == "assistant":
                # Confidence badge
                confidence = msg.get("confidence", 0)
                if confidence > 0:
                    st.markdown(
                        get_confidence_html(confidence),
                        unsafe_allow_html=True
                    )

                # Visual evidence
                evidence = msg.get("evidence", None)
                if evidence and st.session_state.file_image:
                    render_evidence_display(
                        image=st.session_state.file_image,
                        bbox=evidence.get("bbox"),
                        evidence_text=evidence.get("text", "")
                    )
