import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="DocuQuery RAG Assistant", layout="wide")
st.title("DocuQuery — Page-Cited RAG Assistant")

with st.sidebar:
    st.header("Ingest Document")
    doc_title = st.text_input("Document Title", placeholder="e.g., Deloitte Risk Report 2026")
    doc_text = st.text_area("Paste Document Text", height=200)
    if st.button("Index Document", type="primary"):
        if not doc_title.strip() or not doc_text.strip():
            st.warning("Provide both a title and document text.")
        else:
            resp = requests.post(
                f"{API_BASE_URL}/api/v1/documents",
                json={"title": doc_title, "content": doc_text, "source_type": "text"},
                timeout=15,
            )
            if resp.status_code == 201:
                st.success(f"Indexed '{doc_title}' ({resp.json()['chunk_count']} chunks)")
            else:
                st.error(resp.text)

st.subheader("Ask a Question")
question = st.text_input("Question", placeholder="What are the key SLA or risk thresholds?")
top_k = st.slider("Top-K Citations", min_value=1, max_value=5, value=3)

if st.button("Search & Answer"):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/query",
            json={"question": question, "top_k": top_k},
            timeout=25,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.markdown(f"**Answer (`{data['mode']}` mode, {data['latency_ms']} ms):**")
            st.info(data["answer"])
            st.markdown("### Citations")
            for cite in data["citations"]:
                with st.expander(
                    f"{cite['document_title']} — Page {cite['page_number']} (score: {cite['score']})"
                ):
                    st.write(cite["snippet"])
        else:
            st.error(resp.text)
