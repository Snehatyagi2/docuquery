import html
import os
import requests
import streamlit as st

DEFAULT_API_URL = "https://docuquery-api-vs52.onrender.com"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_URL).rstrip("/")

st.set_page_config(
    page_title="DocuQuery — Page-Cited RAG Workbench",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Stitch DocuQuery Design System (Modern Editorial Pragmatism)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    .dq-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 20px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        margin-bottom: 18px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .dq-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .dq-logo {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: linear-gradient(135deg, #4F46E5, #3525CD);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: -0.02em;
    }
    .dq-title {
        font-size: 18px;
        font-weight: 600;
        color: #0F172A;
        margin: 0;
        line-height: 1.2;
    }
    .dq-subtitle {
        font-size: 12px;
        color: #64748B;
        margin: 0;
    }
    .dq-header-actions {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .dq-pill-ok {
        background: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .dq-pill-warn {
        background: #FFFBEB;
        color: #B45309;
        border: 1px solid #FDE68A;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .dq-docs-link {
        background: #F8FAFC;
        color: #334155 !important;
        border: 1px solid #CBD5E1;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        text-decoration: none;
    }
    .dq-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .dq-answer-card {
        background: #FFFFFF;
        border: 1px solid #C7D2FE;
        border-left: 4px solid #4F46E5;
        border-radius: 10px;
        padding: 18px 20px;
        margin: 12px 0 18px 0;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.06);
    }
    .dq-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .dq-badge-indigo {
        background: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .dq-badge-emerald {
        background: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .dq-badge-slate {
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .dq-score-bar-bg {
        width: 100%;
        height: 6px;
        background: #F1F5F9;
        border-radius: 9999px;
        overflow: hidden;
        margin: 8px 0 10px 0;
    }
    .dq-score-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #4F46E5, #10B981);
        border-radius: 9999px;
    }
    .dq-snippet {
        font-size: 13.5px;
        line-height: 1.6;
        color: #334155;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 10px 12px;
    }
    .dq-metric-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
    }
    .dq-metric-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748B;
    }
    .dq-metric-val {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 2px;
    }
    div.stButton > button[kind="primary"] {
        background-color: #4F46E5;
        border-color: #4338CA;
        color: #FFFFFF;
        font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #4338CA;
        border-color: #3730A3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=8)
        return r.status_code == 200
    except Exception:
        return False


def fetch_documents():
    try:
        r = requests.get(f"{API_BASE_URL}/api/v1/documents", timeout=45)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


api_ok = check_api_health()
status_badge = (
    '<span class="dq-pill-ok">● API Connected</span>'
    if api_ok
    else '<span class="dq-pill-warn">● API Waking Up</span>'
)

st.markdown(
    f"""
    <div class="dq-header">
        <div class="dq-brand">
            <div class="dq-logo">DQ</div>
            <div>
                <p class="dq-title">DocuQuery Workbench</p>
                <p class="dq-subtitle">Page-Cited RAG Document Intelligence &amp; Retrieval Evaluation</p>
            </div>
        </div>
        <div class="dq-header-actions">
            {status_badge}
            <a class="dq-docs-link" href="{html.escape(API_BASE_URL)}/docs" target="_blank">Swagger API Docs ↗</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

docs = fetch_documents()

with st.sidebar:
    st.markdown("### Document Corpus")
    st.caption("Upload a PDF or paste text to index page-aware chunks.")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], help="Extracts text per page via pypdf")
    if st.button("Upload & Index PDF", type="primary", use_container_width=True):
        if pdf_file is None:
            st.warning("Select a PDF file first.")
        else:
            with st.spinner("Parsing pages and indexing chunks..."):
                resp = requests.post(
                    f"{API_BASE_URL}/api/v1/documents/upload",
                    files={"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")},
                    timeout=60,
                )
            if resp.status_code == 201:
                data = resp.json()
                st.success(f"Indexed '{data['title']}' ({data['page_count']}p, {data['chunk_count']} chunks)")
                st.rerun()
            else:
                st.error(resp.text)

    with st.expander("Paste Raw Text", expanded=False):
        doc_title = st.text_input("Document Title", placeholder="e.g., Supply Chain SLA Policy")
        doc_text = st.text_area("Document Content", height=130, placeholder="Paste policy or report text...")
        if st.button("Chunk & Index Text", use_container_width=True):
            if not doc_title.strip() or not doc_text.strip():
                st.warning("Provide both a title and text.")
            else:
                with st.spinner("Indexing text..."):
                    resp = requests.post(
                        f"{API_BASE_URL}/api/v1/documents",
                        json={"title": doc_title, "content": doc_text, "source_type": "text"},
                        timeout=60,
                    )
                if resp.status_code == 201:
                    st.success(f"Indexed '{doc_title}'")
                    st.rerun()
                else:
                    st.error(resp.text)

    st.divider()
    st.markdown(f"#### Indexed Documents ({len(docs)})")
    if not docs:
        st.info("No documents indexed yet. Upload a PDF or paste text above.")
    for d in docs:
        col_info, col_del = st.columns([4, 1])
        with col_info:
            st.markdown(f"**{d['title']}**")
            st.caption(f"{d['page_count']} pages · {d['chunk_count']} chunks")
        with col_del:
            if st.button("✕", key=f"del_{d['id']}", help=f"Delete {d['title']}"):
                requests.delete(f"{API_BASE_URL}/api/v1/documents/{d['id']}", timeout=30)
                st.rerun()

tab_query, tab_eval = st.tabs(["RAG Query & Citations", "Retrieval Evaluation Benchmark"])

with tab_query:
    doc_options = {"All Indexed Documents": None}
    for d in docs:
        doc_options[f"{d['title']} ({d['page_count']}p)"] = d["id"]

    q_col, scope_col, k_col = st.columns([3, 1.4, 0.8])
    with q_col:
        question = st.text_input(
            "Ask a question across your documents",
            placeholder="e.g., What is the warehouse dispatch SLA or credit risk weight?",
        )
    with scope_col:
        selected_label = st.selectbox("Document Scope", list(doc_options.keys()))
    with k_col:
        top_k = st.selectbox("Top-K", [3, 5, 10], index=0)

    if st.button("Run RAG Query", type="primary"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            payload = {"question": question, "top_k": top_k}
            if doc_options[selected_label]:
                payload["document_id"] = doc_options[selected_label]

            with st.spinner("Retrieving relevant passages and generating citations..."):
                resp = requests.post(f"{API_BASE_URL}/api/v1/query", json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                citations = data.get("citations", [])
                chips_html = " ".join(
                    f'<span class="dq-badge-indigo">Page {c["page_number"]}</span>'
                    for c in citations
                )
                st.markdown(
                    f"""
                    <div class="dq-answer-card">
                        <div class="dq-card-header">
                            <span style="font-weight: 600; font-size: 14px; color: #0F172A;">
                                Synthesized Grounded Answer
                            </span>
                            <div style="display:flex; gap:8px; align-items:center;">
                                <span class="dq-badge-slate">mode: {html.escape(data['mode'])}</span>
                                <span class="dq-badge-emerald">{data['latency_ms']} ms</span>
                            </div>
                        </div>
                        <p style="font-size: 14.5px; line-height: 1.65; color: #1E293B; margin-bottom: 12px;">
                            {html.escape(data['answer'])}
                        </p>
                        <div>{chips_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(f"#### Retrieved Source Citations ({len(citations)})")
                for rank, cite in enumerate(citations, start=1):
                    pct = min(100, max(5, int(round(cite["score"] * 100))))
                    score_class = "dq-badge-emerald" if cite["score"] >= 0.45 else "dq-badge-indigo"
                    st.markdown(
                        f"""
                        <div class="dq-card">
                            <div class="dq-card-header">
                                <div>
                                    <span class="dq-badge-slate">#{rank}</span>
                                    <strong style="margin-left:8px; color:#0F172A;">{html.escape(cite['document_title'])}</strong>
                                    <span class="dq-badge-indigo" style="margin-left:8px;">Page {cite['page_number']}</span>
                                    <span class="dq-badge-slate" style="margin-left:4px;">Chunk {cite['chunk_index']}</span>
                                </div>
                                <span class="{score_class}">Cosine: {cite['score']:.4f}</span>
                            </div>
                            <div class="dq-score-bar-bg">
                                <div class="dq-score-bar-fill" style="width: {pct}%;"></div>
                            </div>
                            <div class="dq-snippet">{html.escape(cite['snippet'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.error(resp.text)

with tab_eval:
    st.markdown("#### Benchmark Retrieval Quality (`POST /api/v1/evaluate`)")
    st.caption("Evaluate Hit Rate@K, Mean Reciprocal Rank (MRR), and average latency on a labeled query.")

    if not docs:
        st.info("Index at least one document in the sidebar to run a retrieval benchmark.")
    else:
        eval_doc = st.selectbox("Target Document", list(doc_options.keys()), key="eval_doc")
        e_col1, e_col2, e_col3 = st.columns([2.5, 1, 1.5])
        with e_col1:
            eval_q = st.text_input("Test Question", placeholder="e.g., What is the dispatch SLA?")
        with e_col2:
            eval_page = st.number_input("Expected Page", min_value=1, value=1)
        with e_col3:
            eval_kw = st.text_input("Expected Keyword", placeholder="e.g., 4 hours")

        if st.button("Run Evaluation Benchmark", type="primary"):
            if not eval_q.strip():
                st.warning("Enter a test question.")
            else:
                eval_payload = {
                    "top_k": 3,
                    "cases": [
                        {
                            "question": eval_q,
                            "expected_page": int(eval_page),
                            "expected_keyword": eval_kw.strip() or None,
                        }
                    ],
                }
                if doc_options[eval_doc]:
                    eval_payload["document_id"] = doc_options[eval_doc]

                with st.spinner("Evaluating retrieval metrics..."):
                    ev_resp = requests.post(f"{API_BASE_URL}/api/v1/evaluate", json=eval_payload, timeout=60)

                if ev_resp.status_code == 200:
                    m = ev_resp.json()
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.markdown(
                            f'<div class="dq-metric-box"><div class="dq-metric-label">Hit Rate @ 3</div><div class="dq-metric-val">{m["hit_rate_at_k"]*100:.1f}%</div></div>',
                            unsafe_allow_html=True,
                        )
                    with m2:
                        st.markdown(
                            f'<div class="dq-metric-box"><div class="dq-metric-label">MRR</div><div class="dq-metric-val">{m["mrr"]:.3f}</div></div>',
                            unsafe_allow_html=True,
                        )
                    with m3:
                        st.markdown(
                            f'<div class="dq-metric-box"><div class="dq-metric-label">Avg Latency</div><div class="dq-metric-val">{m["avg_latency_ms"]} ms</div></div>',
                            unsafe_allow_html=True,
                        )
                    with m4:
                        st.markdown(
                            f'<div class="dq-metric-box"><div class="dq-metric-label">Cases</div><div class="dq-metric-val">{m["total_cases"]}</div></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.error(ev_resp.text)
