import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.services.document_service import DocumentService


@pytest.fixture
def mocks():
    dense = MagicMock()
    lexical = MagicMock()
    dense.index_corpus.return_value = (["1", "2"], {"status": "success", "count": 2})
    lexical.index_documents.return_value = (
        ["1", "2"],
        {"status": "success", "count": 2},
    )
    return dense, lexical


def create_pdf(path: Path) -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hello PDF", ln=True)
    pdf.output(path)


def create_docx(path: Path) -> None:
    from docx import Document

    doc = Document()
    doc.add_paragraph("Hello DOCX")
    doc.save(path)


def test_parse_various_formats(tmp_path, mocks):
    dense, lexical = mocks
    service = DocumentService(dense, lexical)

    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("hello txt")
    assert "hello txt" in service.parse_document(str(txt_file))

    html_file = tmp_path / "sample.html"
    html_file.write_text("<html><body><p>Hello <b>HTML</b></p></body></html>")
    assert "Hello HTML" in service.parse_document(str(html_file))

    md_file = tmp_path / "sample.md"
    md_file.write_text("# Title\n\nHello MD")
    parsed_md = service.parse_document(str(md_file))
    assert "Title" in parsed_md and "Hello MD" in parsed_md

    if importlib.util.find_spec("fpdf") and importlib.util.find_spec("pypdf"):
        pdf_file = tmp_path / "sample.pdf"
        create_pdf(pdf_file)
        assert "Hello PDF" in service.parse_document(str(pdf_file))

    if importlib.util.find_spec("docx"):
        docx_file = tmp_path / "sample.docx"
        create_docx(docx_file)
        assert "Hello DOCX" in service.parse_document(str(docx_file))


def test_chunk_and_ingest(tmp_path, mocks):
    dense, lexical = mocks
    service = DocumentService(dense, lexical, chunk_size=3, overlap=1)
    file = tmp_path / "text.txt"
    file.write_text("one two three four five")
    result = service.ingest([str(file)])

    expected_chunks = ["one two three", "three four five"]
    assert dense.index_corpus.call_args[0][0] == expected_chunks
    assert lexical.index_documents.call_args[0][0] == expected_chunks
    assert result["dense"]["count"] == 2
    assert result["lexical"]["count"] == 2
