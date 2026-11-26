import os
import requests
import streamlit as st

DEFAULT_API_URL = "https://docuquery-api-vs52.onrender.com"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_URL).rstrip("/")

st.set_page_config(page_title="DocuQuery RAG Assistant", layout="wide")
st.title("DocuQuery — Page-Cited RAG Assistant")
st.caption(f"Connected to API: `{API_BASE_URL}` (first request after idle may take ~30s on free tier)")

with st.sidebar:
    st.header("1. Upload PDF")
    pdf_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if st.button("Upload & Index PDF") and pdf_file is not None:
        with st.spinner("Indexing PDF..."):
            resp = requests.post(
                f"{API_BASE_URL}/api/v1/documents/upload",
                files={"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")},
                timeout=60,
            )
        if resp.status_code == 201:
            data = resp.json()
            st.success(f"Indexed '{data['title']}' ({data['page_count']} pages, {data['chunk_count']} chunks)")
        else:
            st.error(resp.text)

    st.divider()
    st.header("2. Or Paste Text")
    doc_title = st.text_input("Document Title", placeholder="e.g., Deloitte Risk Report 2026")
    doc_text = st.text_area("Paste Document Text", height=160)
    if st.button("Index Text", type="primary"):
        if not doc_title.strip() or not doc_text.strip():
            st.warning("Provide both a title and document text.")
        else:
            with st.spinner("Indexing text..."):
                resp = requests.post(
                    f"{API_BASE_URL}/api/v1/documents",
                    json={"title": doc_title, "content": doc_text, "source_type": "text"},
                    timeout=60,
                )
            if resp.status_code == 201:
                st.success(f"Indexed '{doc_title}' ({resp.json()['chunk_count']} chunks)")
            else:
                st.error(resp.text)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Ask a Question")
    question = st.text_input("Question", placeholder="What are the key SLA or risk thresholds?")
    top_k = st.slider("Top-K Citations", min_value=1, max_value=5, value=3)

    if st.button("Search & Answer"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Retrieving citations..."):
                resp = requests.post(
                    f"{API_BASE_URL}/api/v1/query",
                    json={"question": question, "top_k": top_k},
                    timeout=60,
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

with col2:
    st.subheader("Indexed Documents")
    try:
        docs_resp = requests.get(f"{API_BASE_URL}/api/v1/documents", timeout=60)
        if docs_resp.status_code == 200:
            docs = docs_resp.json()
            if not docs:
                st.write("No documents indexed yet. Upload a PDF or paste text in the sidebar.")
            for d in docs:
                st.markdown(f"- **{d['title']}** ({d['page_count']}p, {d['chunk_count']} chunks)")
        else:
            st.warning("Could not fetch documents.")
    except Exception as exc:
        st.warning(f"API waking up or unreachable: {exc}")
