import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FinDoc AI",
    page_icon="📄",
    layout="wide"
)

st.title("📄 FinDoc AI")
st.caption("AI Agent για Q&A σε τιμολόγια και αποδείξεις")

if "doc_id" not in st.session_state:
    st.session_state.doc_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader(
    "Ανέβασε τιμολόγιο ή απόδειξη",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    if st.button("Analyze document"):
        with st.spinner("Ανάλυση εγγράφου με Azure Document Intelligence..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            response = requests.post(
                f"{BACKEND_URL}/documents/analyze",
                files=files
            )

            if response.status_code != 200:
                st.error(response.text)
            else:
                data = response.json()
                st.session_state.doc_id = data["doc_id"]
                st.session_state.messages = []

                st.success(f"Document analyzed: {data['filename']}")
                st.write("Document ID:", data["doc_id"])
                st.write("Chunks:", data["chunk_count"])

                st.subheader("Extracted fields")
                st.json(data["fields"])

                st.subheader("Line items")
                st.json(data["line_items"])

if st.session_state.doc_id:
    st.divider()
    st.subheader("Chat με το τιμολόγιο")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_question = st.chat_input("Ρώτα κάτι για το τιμολόγιο...")

    if user_question:
        st.session_state.messages.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.write(user_question)

        with st.spinner("Ο agent ψάχνει μόνο μέσα στο έγγραφο..."):
            response = requests.post(
                f"{BACKEND_URL}/ask",
                json={
                    "doc_id": st.session_state.doc_id,
                    "question": user_question
                }
            )

            if response.status_code != 200:
                answer = response.text
            else:
                data = response.json()
                answer = data["answer"]

                if data.get("sources"):
                    answer += "\n\n---\nΠηγές:\n"
                    for source in data["sources"]:
                        answer += (
                            f"\n- File: {source.get('filename')}, "
                            f"Page: {source.get('page')}, "
                            f"Score: {source.get('score'):.3f}\n"
                            f"  Απόσπασμα: {source.get('source_text')}\n"
                        )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            with st.chat_message("assistant"):
                st.write(answer)
else:
    st.info("Ανέβασε πρώτα ένα invoice/receipt για να ξεκινήσει το chat.")