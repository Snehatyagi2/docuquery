from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class PageInput(BaseModel):
    """Single document page payload."""

    page_number: int = Field(..., ge=1, description="1-based page number")
    text: str = Field(..., min_length=1, description="Extracted text content of the page")


class DocumentCreateRequest(BaseModel):
    """Request body for ingesting a document via raw text or structured pages."""

    title: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(default="text", max_length=50)
    content: Optional[str] = Field(default=None, description="Single-block text content (treated as page 1)")
    pages: Optional[List[PageInput]] = Field(default=None, description="Multi-page structured text")

    @model_validator(mode="after")
    def validate_content_or_pages(self) -> "DocumentCreateRequest":
        has_content = bool(self.content and self.content.strip())
        has_pages = bool(self.pages)
        if not has_content and not has_pages:
            raise ValueError("Either 'content' or non-empty 'pages' must be provided.")
        return self


class DocumentResponse(BaseModel):
    """Metadata returned for an ingested document."""

    id: str
    title: str
    source_type: str
    page_count: int
    chunk_count: int
    created_at: datetime


class QueryRequest(BaseModel):
    """RAG question-answering request."""

    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    document_id: Optional[str] = Field(default=None, description="Optional filter to query a single document")


class Citation(BaseModel):
    """Retrieved passage supporting the generated answer."""

    document_id: str
    document_title: str
    page_number: int
    chunk_index: int
    score: float
    snippet: str


class QueryResponse(BaseModel):
    """RAG response containing the answer, page citations, and latency."""

    question: str
    answer: str
    mode: str
    latency_ms: float
    citations: List[Citation]


class EvalCase(BaseModel):
    """Single labeled evaluation case for retrieval quality."""

    question: str = Field(..., min_length=3)
    expected_page: Optional[int] = Field(default=None, ge=1)
    expected_keyword: Optional[str] = Field(default=None, min_length=1)


class EvaluateRequest(BaseModel):
    """Batch retrieval evaluation request."""

    document_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)
    cases: List[EvalCase] = Field(..., min_length=1)


class EvaluateResponse(BaseModel):
    """Aggregate retrieval metrics across evaluation cases."""

    total_cases: int
    hit_rate_at_k: float
    mrr: float
    avg_latency_ms: float
