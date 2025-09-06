import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from src.retrieval.dense import DenseRetriever
from src.retrieval.lexical import LexicalBM25


class DocumentService:
    """Handle document parsing, chunking, and indexing."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        lexical_retriever: LexicalBM25,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.chunk_size = chunk_size
        self.overlap = overlap

    # Parsing helpers
    def parse_document(self, file_path: str) -> str:
        """Parse a document from various formats into plain text."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                try:
                    from pypdf import PdfReader
                except Exception as exc:  # pragma: no cover
                    raise RuntimeError("pypdf is required for PDF parsing") from exc
                with path.open("rb") as fh:
                    reader = PdfReader(fh)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
            elif suffix == ".docx":
                try:
                    from docx import Document  # type: ignore
                except Exception as exc:  # pragma: no cover
                    raise RuntimeError(
                        "python-docx is required for DOCX parsing"
                    ) from exc
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs)
            elif suffix in {".txt", ".md", ".html", ".htm"}:
                with path.open("r", encoding="utf-8", errors="ignore") as fh:
                    data = fh.read()
                if suffix in {".html", ".htm"}:
                    text = self._html_to_text(data)
                elif suffix == ".md":
                    text = self._markdown_to_text(data)
                else:
                    text = data
            else:
                raise ValueError(f"Unsupported file type: {suffix}")
            return text.strip()
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to parse %s: %s", path, exc)
            raise

    def _html_to_text(self, data: str) -> str:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(data, "html.parser")
            return soup.get_text(separator=" ")
        except Exception:  # pragma: no cover
            return re.sub(r"<[^>]+>", " ", data)

    def _markdown_to_text(self, data: str) -> str:
        try:
            import markdown

            html = markdown.markdown(data)
            return self._html_to_text(html)
        except Exception:  # pragma: no cover
            return data

    # Chunking
    def chunk_text(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks: List[str] = []
        step = max(self.chunk_size - self.overlap, 1)
        for start in range(0, len(words), step):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
        return chunks

    # Ingestion
    def ingest(self, file_paths: List[str]) -> Dict[str, Any]:
        """Parse files, chunk text, and update both indexes."""
        all_chunks: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        for file_path in file_paths:
            text = self.parse_document(file_path)
            chunks = self.chunk_text(text)
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                metadatas.append({"source": str(file_path), "chunk": idx})
        dense_ids, dense_meta = self.dense_retriever.index_corpus(all_chunks, metadatas)
        lexical_ids, lexical_meta = self.lexical_retriever.index_documents(all_chunks)
        return {
            "dense": {"ids": dense_ids, **dense_meta},
            "lexical": {"ids": lexical_ids, **lexical_meta},
        }
