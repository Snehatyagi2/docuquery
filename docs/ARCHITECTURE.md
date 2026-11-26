# DocuQuery Technical Architecture

## 1. Ingestion & Page-Aware Chunking (`app/rag.py`)
- PDFs uploaded to `POST /api/v1/documents/upload` are parsed page-by-page using `pypdf.PdfReader`.
- Each page's whitespace is normalized and split by `chunk_pages()` into sliding windows (`CHUNK_SIZE=500` characters, `CHUNK_OVERLAP=100` characters).
- Every chunk stores `(document_id, page_number, chunk_index, content)` in SQLAlchemy (`SQLite` by default, `PostgreSQL` via `DATABASE_URL`).

## 2. Retrieval (`retrieve_top_chunks`)
- Chunks are vectorized at query time using `sklearn.feature_extraction.text.TfidfVectorizer(stop_words="english")` and ranked via cosine similarity.
- Only chunks with similarity `score > 0.0` are returned, up to `top_k`.
- **Why TF-IDF first?** Zero external API cost, deterministic results, sub-20ms retrieval latency on small-to-medium document sets, and zero heavy C++ vector-DB build dependencies.

## 3. Answer Synthesis (`synthesize_answer`)
- **LLM Mode (`gemini`):** When `GEMINI_API_KEY` is configured, DocuQuery calls the Gemini REST API (`gemini-2.5-flash` by default) with a strict grounding prompt requiring inline `[Document Title, Page X]` citations.
- **Extractive Mode (`extractive`):** If no API key is set (or if the external call fails), DocuQuery returns the highest-scoring passage directly with its document title and page number.

## 4. Retrieval Evaluation (`POST /api/v1/evaluate`)
For a batch of labeled `(question, expected_page, expected_keyword)` cases:
- **Hit Rate@K:** Fraction of queries where at least one of the top-$K$ retrieved chunks matches `expected_page` and `expected_keyword`.
- **Mean Reciprocal Rank (MRR):** Average of $\frac{1}{\text{rank}}$ of the first matching chunk across all cases (`0.0` if not found in top-$K$).
- **Average Latency (ms):** Mean retrieval execution time per query.
