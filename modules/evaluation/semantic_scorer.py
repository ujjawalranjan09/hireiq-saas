"""Semantic similarity scoring using sentence-transformers."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model
_model = None


def _get_model():
    """Lazily load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import SENTENCE_TRANSFORMER_MODEL
            logger.info(f"Loading sentence transformer: {SENTENCE_TRANSFORMER_MODEL}")
            _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        except ImportError:
            logger.warning("sentence-transformers not available, using fallback")
            _model = False
    return _model if _model else None


def compute_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts.
    
    Args:
        text1: First text.
        text2: Second text.
        
    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not text1.strip() or not text2.strip():
        return 0.0

    model = _get_model()
    if model:
        try:
            embeddings = model.encode([text1, text2])
            from numpy import dot
            from numpy.linalg import norm
            similarity = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
            return float(max(0.0, min(1.0, similarity)))
        except Exception as e:
            logger.warning(f"Sentence transformer similarity failed: {e}")

    return _fallback_similarity(text1, text2)


def compute_similarity_batch(texts: List[str], reference: str) -> List[float]:
    """Compute similarity of multiple texts against a reference.
    
    Args:
        texts: List of texts to compare.
        reference: Reference text.
        
    Returns:
        List of similarity scores.
    """
    if not reference.strip():
        return [0.0] * len(texts)

    model = _get_model()
    if model:
        try:
            all_texts = [reference] + texts
            embeddings = model.encode(all_texts)
            ref_embedding = embeddings[0]
            from numpy import dot
            from numpy.linalg import norm
            ref_norm = norm(ref_embedding)
            scores = []
            for emb in embeddings[1:]:
                sim = dot(ref_embedding, emb) / (ref_norm * norm(emb))
                scores.append(float(max(0.0, min(1.0, sim))))
            return scores
        except Exception as e:
            logger.warning(f"Batch similarity failed: {e}")

    return [_fallback_similarity(reference, text) for text in texts]


def _fallback_similarity(text1: str, text2: str) -> float:
    """Fallback similarity using Jaccard index on word sets."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def compute_embedding(text: str) -> Optional[list]:
    """Compute embedding vector for a text.
    
    Args:
        text: Input text.
        
    Returns:
        Embedding vector as list, or None if model unavailable.
    """
    model = _get_model()
    if model:
        try:
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.warning(f"Embedding computation failed: {e}")
    return None
