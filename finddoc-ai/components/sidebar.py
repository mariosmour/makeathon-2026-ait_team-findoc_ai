
import streamlit as st
from PIL import Image
from utils.api import get_auto_summary, upload_document
import io


def render_sidebar():
    """Render the sidebar with upload and document info"""

    with st.sidebar:
        # Logo / Branding
        st.markdown("### 🏦 CloudFin")
        st.markdown("*FinDoc AI Agent*")
        st.divider()

        # File Upload Section
        st.markdown("#### 📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Drop your invoice or receipt here",
            type=["pdf", "png", "jpg", "jpeg"],
            help="Supported: PDF, PNG, JPG"
        )

        if uploaded_file is not None:
            file_key = uploaded_file.name

            # Process new upload
            if file_key not in st.session_state.uploaded_files:
                with st.spinner("📤 Processing document..."):
                    # Upload to backend and get file_id
                    result = upload_document(uploaded_file)

                    st.session_state.uploaded_files[file_key] = {
                        "file_id": result["file_id"],
                        "filename": uploaded_file.name,
                        "summary": result.get("summary", None)
                    }
                    st.session_state.current_file_id = result["file_id"]

                    # Store image for evidence rendering
                    if uploaded_file.type.startswith("image"):
                        st.session_state.file_image = Image.open(
                            io.BytesIO(uploaded_file.getvalue())
                        )
                    else:
                        # For PDF, backend should return first page as image
                        st.session_state.file_image = result.get(
                            "page_image", None
                        )

                    # Clear previous chat
                    st.session_state.messages = []

            # Show upload success
            st.success(f"✅ **{uploaded_file.name}**")

            # Document preview
            if uploaded_file.type.startswith("image"):
                st.image(uploaded_file, use_container_width=True)

            # Auto-summary card
            file_data = st.session_state.uploaded_files[file_key]
            if file_data.get("summary"):
                st.divider()
                st.markdown("#### 📊 Auto-Summary")
                summary = file_data["summary"]
                st.markdown(f"""
                | Field | Value |
                |-------|-------|
                | **Vendor** | {summary.get('vendor', 'N/A')} |
                | **Amount** | {summary.get('total', 'N/A')} |
                | **Date** | {summary.get('date', 'N/A')} |
                | **Items** | {summary.get('line_items_count', 'N/A')} |
                """)

                # Alerts
                if summary.get("alerts"):
                    st.divider()
                    st.markdown("#### ⚠️ Alerts")
                    for alert in summary["alerts"]:
                        st.warning(alert)

        # Bottom info
        st.divider()
        st.markdown("#### 💡 Example Questions")
        st.markdown("""
        - Ποιο είναι το συνολικό ποσό;
        - What's the vendor name?
        - List all line items
        - Ποια η ημερομηνία έκδοσης;
        - Is there VAT included?
        """)

        st.divider()
        st.caption("🔒 Zero Hallucinations | 📍 Visual Evidence | 🧠 AI-Powered")
