"""Document retriever for job descriptions — chunking, embedding, and similarity search."""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded sentence transformer
_model = None


def _get_model():
    """Lazily load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import SENTENCE_TRANSFORMER_MODEL
            _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            logger.info(f"Loaded embedding model: {SENTENCE_TRANSFORMER_MODEL}")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
    return _model


@dataclass
class DocumentChunk:
    """A chunk of a document with its embedding."""
    text: str
    chunk_id: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }


class Retriever:
    """Retrieval engine for job description documents.

    Chunks documents, creates embeddings, and retrieves the most relevant
    chunks for a given query using cosine similarity.

    Args:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._chunks: List[DocumentChunk] = []
        self._embeddings_matrix: Optional[np.ndarray] = None

    @property
    def chunk_count(self) -> int:
        """Number of indexed chunks."""
        return len(self._chunks)

    @property
    def is_ready(self) -> bool:
        """Whether the retriever has indexed documents."""
        return self._embeddings_matrix is not None and len(self._chunks) > 0

    def load_document(
        self,
        text: str,
        source: str = "job_description",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Load and index a document from raw text.

        Args:
            text: The document text.
            source: Label for the document source.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            Number of chunks created.
        """
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty")

        base_metadata = metadata or {}
        base_metadata["source"] = source

        # Clean and split into chunks
        cleaned = self._clean_text(text)
        raw_chunks = self._split_into_chunks(cleaned)

        model = _get_model()

        # Create document chunks with embeddings
        chunks: List[DocumentChunk] = []
        embeddings_list: List[np.ndarray] = []

        # Encode all at once for efficiency
        if raw_chunks:
            encoded = model.encode(raw_chunks, show_progress_bar=False, normalize_embeddings=True)
            for i, (chunk_text, emb) in enumerate(zip(raw_chunks, encoded)):
                chunk = DocumentChunk(
                    text=chunk_text,
                    chunk_id=i,
                    metadata={**base_metadata, "chunk_index": i},
                    embedding=emb,
                )
                chunks.append(chunk)
                embeddings_list.append(emb)

        self._chunks = chunks
        if embeddings_list:
            self._embeddings_matrix = np.array(embeddings_list)
        else:
            self._embeddings_matrix = None

        logger.info(f"Indexed {len(chunks)} chunks from '{source}'")
        return len(chunks)

    def load_from_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Load a document from a file.

        Supports .txt, .md, and .pdf files.

        Args:
            file_path: Path to the document.
            metadata: Optional metadata.

        Returns:
            Number of chunks created.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            text = self._read_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        source = os.path.basename(file_path)
        return self.load_document(text, source=source, metadata=metadata)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.15,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The search query.
            top_k: Number of results to return.
            min_similarity: Minimum cosine similarity threshold.

        Returns:
            List of (DocumentChunk, similarity_score) tuples sorted by relevance.
        """
        if not self.is_ready:
            logger.warning("Retriever has no indexed documents")
            return []

        model = _get_model()
        query_embedding = model.encode([query], normalize_embeddings=True)[0]

        # Cosine similarity (embeddings are already normalized)
        similarities = self._embeddings_matrix @ query_embedding

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results: List[Tuple[DocumentChunk, float]] = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_similarity:
                results.append((self._chunks[idx], score))

        return results

    def retrieve_requirements(
        self,
        candidate_skills: List[str],
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """Retrieve job requirements relevant to candidate skills.

        Args:
            candidate_skills: List of skills from the candidate's resume.
            top_k: Max results per skill.

        Returns:
            List of (DocumentChunk, score, matched_skill) tuples.
        """
        all_results: List[Tuple[DocumentChunk, float, str]] = []

        for skill in candidate_skills:
            query = f"job requirement experience {skill}"
            results = self.retrieve(query, top_k=max(2, top_k // len(candidate_skills)))
            for chunk, score in results:
                # Avoid duplicates
                if not any(c.chunk_id == chunk.chunk_id for c, _, _ in all_results):
                    all_results.append((chunk, score, skill))

        # Sort by score descending and trim
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]

    def get_all_text(self) -> str:
        """Get the full text of all indexed chunks."""
        return "\n\n".join(chunk.text for chunk in self._chunks)

    def clear(self) -> None:
        """Clear all indexed documents."""
        self._chunks = []
        self._embeddings_matrix = None

    # ── Internal methods ──────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """Clean and normalize document text."""
        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks, preferring sentence boundaries."""
        if len(text) <= self.chunk_size:
            return [text]

        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= self.chunk_size:
                current = f"{current} {sentence}".strip() if current else sentence
            else:
                if current:
                    chunks.append(current)
                # If a single sentence exceeds chunk_size, split it
                if len(sentence) > self.chunk_size:
                    for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                        chunks.append(sentence[i : i + self.chunk_size])
                    current = ""
                else:
                    current = sentence

        if current:
            chunks.append(current)

        # Add overlap: prepend tail of previous chunk
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_tail = chunks[i - 1][-self.chunk_overlap :]
                overlapped.append(f"{prev_tail} {chunks[i]}".strip())
            chunks = overlapped

        return chunks

    @staticmethod
    def _read_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            import pdfplumber

            text_parts: List[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError:
            pass

        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise ImportError("Install pdfplumber or PyPDF2 to read PDF files")
