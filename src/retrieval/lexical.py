import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi

try:  # pragma: no cover - optional dependency
    from nltk.stem import PorterStemmer
except Exception:  # pragma: no cover
    PorterStemmer = None  # type: ignore


Tokenizer = Callable[[str], List[str]]


def default_tokenizer(text: str) -> List[str]:
    """Simple regex-based tokenizer."""
    return re.findall(r"\b\w+\b", text.lower())


class LexicalBM25:
    """Lexical retrieval using BM25Okapi with optional stemming."""

    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        enable_stemming: bool = False,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.tokenizer = tokenizer or default_tokenizer
        self.enable_stemming = enable_stemming and PorterStemmer is not None
        self.stemmer = PorterStemmer() if self.enable_stemming else None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

        if enable_stemming and PorterStemmer is None:
            self._logger.warning(
                "Stemming requested but " "nltk not available; disabling"
            )

    def _preprocess(self, text: str) -> List[str]:
        tokens = self.tokenizer(text)
        if self.stemmer:
            tokens = [self.stemmer.stem(tok) for tok in tokens]
        return tokens

    def index_documents(
        self,
        documents: List[str],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Add documents to the BM25 index."""
        try:
            start = len(self.documents)
            ids = []
            for i, doc in enumerate(documents):
                doc_id = str(start + i)
                self.documents.append(doc)
                self.doc_ids.append(doc_id)
                self.corpus_tokens.append(self._preprocess(doc))
                ids.append(doc_id)
            if self.corpus_tokens:
                self.bm25 = BM25Okapi(self.corpus_tokens)
            return ids, {"status": "success", "count": len(ids)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to index documents: %s", exc)
            return [], {"status": "error", "error": str(exc)}

    def query(
        self, query: str, top_k: int = 5
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
        """Query the index and return doc IDs with BM25 scores."""
        try:
            if not self.bm25:
                return [], {"status": "empty"}
            tokens = self._preprocess(query)
            scores = self.bm25.get_scores(tokens)
            ranked = sorted(
                zip(self.doc_ids, scores), key=lambda x: x[1], reverse=True
            )[:top_k]
            return ranked, {"retrieved": len(ranked)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("BM25 query failed: %s", exc)
            return [], {"status": "error", "error": str(exc)}
