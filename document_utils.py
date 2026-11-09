import csv
import io
from pathlib import Path

from docx import Document
from openpyxl import load_workbook


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".py", ".html", ".xml"}
IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


def prepare_document(filename: str, mime_type: str, data: bytes) -> tuple[bytes | None, str | None, str | None]:
    """Return inline media or extracted text for supported Telegram attachments."""
    extension = Path(filename or "").suffix.lower()
    if mime_type in IMAGE_MIME_TYPES:
        return data, mime_type, None
    if mime_type == "application/pdf" or extension == ".pdf":
        return data, "application/pdf", None

    if extension in TEXT_EXTENSIONS or mime_type.startswith("text/"):
        text = data.decode("utf-8-sig", errors="replace")
        if extension == ".csv" or "csv" in mime_type:
            rows = list(csv.reader(io.StringIO(text)))
            text = "\n".join(" | ".join(row) for row in rows)
        return None, None, text[:100_000]

    if extension == ".docx":
        document = Document(io.BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        for table in document.tables:
            for row in table.rows:
                text += "\n" + " | ".join(cell.text for cell in row.cells)
        return None, None, text[:100_000]

    if extension == ".xlsx":
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        lines = []
        for sheet in workbook.worksheets:
            lines.append(f"[ورقة العمل: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                lines.append(" | ".join("" if value is None else str(value) for value in row))
        workbook.close()
        return None, None, "\n".join(lines)[:100_000]

    raise ValueError(
        "نوع الملف غير مدعوم. أرسل صورة أو PDF أو ملف TXT/CSV/JSON/MD أو DOCX أو XLSX."
    )
