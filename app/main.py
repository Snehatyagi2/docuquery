from contextlib import asynccontextmanager
import importlib.util
import io
import time
from typing import List
import uuid

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import ChunkModel, DocumentModel, get_db, init_db
from app.rag import chunk_pages, retrieve_top_chunks, synthesize_answer
from app.schemas import (
    Citation,
    DocumentCreateRequest,
    DocumentResponse,
    EvaluateRequest,
    EvaluateResponse,
    PageInput,
    QueryRequest,
    QueryResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Page-cited RAG API with SQLite/PostgreSQL persistence and REST endpoints.",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
def health_check():
    """Service health endpoint."""
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@app.post(
    "/api/v1/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
def ingest_document(payload: DocumentCreateRequest, db: Session = Depends(get_db)):
    """Ingest raw text or multi-page content into page-aware chunks."""
    pages = payload.pages or [PageInput(page_number=1, text=payload.content or "")]
    raw_chunks = chunk_pages(pages, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
    if not raw_chunks:
        raise HTTPException(status_code=400, detail="No indexable text found in document.")

    doc_id = str(uuid.uuid4())
    doc = DocumentModel(
        id=doc_id,
        title=payload.title.strip(),
        source_type=payload.source_type,
        page_count=len(pages),
    )
    db.add(doc)

    for page_num, chunk_idx, text in raw_chunks:
        db.add(
            ChunkModel(
                id=f"{doc_id}:{chunk_idx}",
                document_id=doc_id,
                page_number=page_num,
                chunk_index=chunk_idx,
                content=text,
            )
        )

    db.commit()
    db.refresh(doc)
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        page_count=doc.page_count,
        chunk_count=len(raw_chunks),
        created_at=doc.created_at,
    )


@app.get("/api/v1/documents", response_model=List[DocumentResponse], tags=["Documents"])
def list_documents(db: Session = Depends(get_db)):
    """List all indexed documents."""
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    return [
        DocumentResponse(
            id=d.id,
            title=d.title,
            source_type=d.source_type,
            page_count=d.page_count,
            chunk_count=len(d.chunks),
            created_at=d.created_at,
        )
        for d in docs
    ]


@app.delete("/api/v1/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its indexed chunks."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(doc)
    db.commit()


@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG"])
def query_documents(payload: QueryRequest, db: Session = Depends(get_db)):
    """Retrieve top-k relevant passages and return a page-cited answer."""
    started = time.perf_counter()
    query = db.query(ChunkModel)
    if payload.document_id:
        query = query.filter(ChunkModel.document_id == payload.document_id)

    chunks = query.all()
    if not chunks:
        raise HTTPException(status_code=404, detail="No indexed chunks found to query.")

    ranked = retrieve_top_chunks(payload.question, chunks, top_k=payload.top_k)
    citations = [
        Citation(
            document_id=chunk.document_id,
            document_title=chunk.document.title,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            score=score,
            snippet=chunk.content,
        )
        for chunk, score in ranked
    ]

    answer, mode = synthesize_answer(payload.question, citations)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return QueryResponse(
        question=payload.question,
        answer=answer,
        mode=mode,
        latency_ms=latency_ms,
        citations=citations,
    )


@app.post("/api/v1/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
def evaluate_retrieval(payload: EvaluateRequest, db: Session = Depends(get_db)):
    """Measure Hit Rate@K, Mean Reciprocal Rank (MRR), and average latency."""
    query = db.query(ChunkModel)
    if payload.document_id:
        query = query.filter(ChunkModel.document_id == payload.document_id)
    chunks = query.all()
    if not chunks:
        raise HTTPException(status_code=404, detail="No indexed chunks found to evaluate.")

    hits = 0
    reciprocal_ranks: List[float] = []
    latencies: List[float] = []

    for case in payload.cases:
        started = time.perf_counter()
        ranked = retrieve_top_chunks(case.question, chunks, top_k=payload.top_k)
        latencies.append((time.perf_counter() - started) * 1000)

        matched_rank = 0
        for idx, (chunk, _) in enumerate(ranked, start=1):
            page_ok = case.expected_page is None or chunk.page_number == case.expected_page
            kw_ok = (
                case.expected_keyword is None
                or case.expected_keyword.lower() in chunk.content.lower()
            )
            if page_ok and kw_ok:
                matched_rank = idx
                break

        if matched_rank > 0:
            hits += 1
            reciprocal_ranks.append(1.0 / matched_rank)
        else:
            reciprocal_ranks.append(0.0)

    total = len(payload.cases)
    return EvaluateResponse(
        total_cases=total,
        hit_rate_at_k=round(hits / total, 4),
        mrr=round(sum(reciprocal_ranks) / total, 4),
        avg_latency_ms=round(sum(latencies) / total, 2),
    )


if importlib.util.find_spec("multipart") is not None and importlib.util.find_spec("pypdf") is not None:
    from fastapi import File, UploadFile
    from pypdf import PdfReader

    @app.post(
        "/api/v1/documents/upload",
        response_model=DocumentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Documents"],
    )
    async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
        """Extract text per page from an uploaded PDF and index it for RAG."""
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are supported.")
        raw_bytes = await file.read()
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [
            PageInput(page_number=i + 1, text=page.extract_text() or "")
            for i, page in enumerate(reader.pages)
            if (page.extract_text() or "").strip()
        ]
        if not pages:
            raise HTTPException(status_code=400, detail="No extractable text found in PDF.")
        req = DocumentCreateRequest(
            title=file.filename or "Uploaded PDF",
            source_type="pdf",
            pages=pages,
        )
        return ingest_document(req, db)
