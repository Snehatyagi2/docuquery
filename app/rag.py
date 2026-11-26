import httpx
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.database import ChunkModel
from app.schemas import Citation, PageInput


def chunk_pages(pages: List[PageInput], chunk_size: int = 500, overlap: int = 100) -> List[Tuple[int, int, str]]:
    """Split pages into overlapping character chunks while preserving page numbers."""
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: List[Tuple[int, int, str]] = []
    global_idx = 0
    step = max(1, chunk_size - overlap)

    for page in pages:
        cleaned = " ".join(page.text.split())
        if not cleaned:
            continue
        start = 0
        while start < len(cleaned):
            end = start + chunk_size
            piece = cleaned[start:end].strip()
            if piece:
                chunks.append((page.page_number, global_idx, piece))
                global_idx += 1
            if end >= len(cleaned):
                break
            start += step
    return chunks


def retrieve_top_chunks(
    question: str,
    chunks: List[ChunkModel],
    top_k: int = 3,
) -> List[Tuple[ChunkModel, float]]:
    """Rank chunks against the question using TF-IDF cosine similarity."""
    if not chunks:
        return []

    corpus = [c.content for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        doc_matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([question])
    except ValueError:
        return [(c, 0.0) for c in chunks[:top_k]]

    scores = cosine_similarity(query_vec, doc_matrix).flatten()
    ranked_indices = scores.argsort()[::-1][:top_k]
    return [(chunks[i], round(float(scores[i]), 4)) for i in ranked_indices if scores[i] > 0.0]


def synthesize_answer(question: str, citations: List[Citation]) -> Tuple[str, str]:
    """Generate a cited answer via Gemini REST API when configured, else extractive fallback."""
    if not citations:
        return "No relevant passages were found in the indexed documents for this question.", "extractive"

    context_block = "\n\n".join(
        f"[{c.document_title} | Page {c.page_number}]: {c.snippet}" for c in citations
    )

    if settings.gemini_api_key:
        prompt = (
            "Answer the question strictly using the provided context. "
            "Cite sources inline as [Document Title, Page X]. "
            "If the context is insufficient, state what is missing.\n\n"
            f"Context:\n{context_block}\n\nQuestion: {question}"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        try:
            resp = httpx.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20.0,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text, "gemini"
        except Exception:
            pass

    top = citations[0]
    answer = (
        f"Based on {top.document_title} (Page {top.page_number}): {top.snippet}"
    )
    return answer, "extractive"
