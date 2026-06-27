"""PDF text extraction."""
from __future__ import annotations

import io

from pypdf import PdfReader


def extract_pdf_text(data: bytes) -> str:
    """Extract text from a PDF byte stream. Best-effort; tolerates partial reads."""
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            parts.append(text)
    return "\n\n".join(parts)