import streamlit as st
import requests
import mimetypes
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_SECRET_KEY", "")
HEADERS = {"X-API-Key": API_KEY}

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Policy Assistant", page_icon="📄")
st.title("📄 DocuMind-A Policy Assistant")


if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar
with st.sidebar:
    st.header("Documents")

    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        if st.button("Upload & Process"):
            with st.spinner("Processing document..."):
                mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), mime_type or "application/octet-stream")}
                response = requests.post(f"{API_URL}/documents/upload", files=files, headers=HEADERS)
                if response.status_code == 200:
                    st.success(f"Uploaded: {response.json()['filename']}")
                else:
                    st.error(f"Upload failed: {response.text}")

    st.divider()
    url_input = st.text_input("Or add a webpage URL")
    if url_input:
        if st.button("Ingest URL"):
            with st.spinner("Fetching and processing webpage..."):
                response = requests.post(f"{API_URL}/documents/upload-url", json={"url": url_input},headers=HEADERS)
                if response.status_code == 200:
                    st.success(f"Added: {response.json()['filename']}")
                else:
                    st.error(f"Failed: {response.text}")

    if st.button("Refresh document list"):
        st.rerun()

    docs_response = requests.get(f"{API_URL}/documents/",headers=HEADERS)
    if docs_response.status_code == 200:
        documents = docs_response.json()
        for doc in documents:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {doc['filename']} ({doc['status']})")
            with col2:
                if st.button("🗑️", key=f"delete_{doc['document_id']}"):
                    requests.delete(f"{API_URL}/documents/{doc['document_id']}",headers=HEADERS)
                    st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for src in msg["sources"]:
                    st.caption(f"{src['source']} — page {src['page']}")

question = st.chat_input("Ask a question about your documents...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            payload = {
                "question": question,
                "top_k": 3,
                "session_id": st.session_state.session_id,
            }
            response = requests.post(f"{API_URL}/chat/ask", json=payload,headers=HEADERS)

            if response.status_code == 200:
                data = response.json()
                st.session_state.session_id = data["session_id"]
                st.write(data["answer"])
                if data.get("sources"):
                    with st.expander("Sources"):
                        for src in data["sources"]:
                            st.caption(f"{src['source']} — page {src['page']}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data.get("sources"),
                })
            else:
                st.error(f"Error: {response.text}")