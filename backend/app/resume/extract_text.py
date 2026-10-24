from io import BytesIO
from pathlib import Path


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _pdf_text(data)
    if lower.endswith(".docx"):
        return _docx_text(data)
    if lower.endswith(".txt"):
        return data.decode("utf-8", errors="replace")
    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")


def extract_text_from_path(path: Path) -> str:
    return extract_text_from_bytes(path.name, path.read_bytes())


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def _docx_text(data: bytes) -> str:
    from docx import Document

    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
