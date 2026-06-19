from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from datetime import datetime

from config import EXPORTS_DIR
from models import TranscriptionResult


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def generate_docx(result: TranscriptionResult, original_filename: str) -> Path:
    doc = Document()

    title = doc.add_heading(f"Transcription: {original_filename}", level=1)
    doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph(f"Model: {result.model}")
    doc.add_paragraph("")

    for seg in result.segments:
        p = doc.add_paragraph()
        ts_run = p.add_run(f"[{format_timestamp(seg.start)} - {format_timestamp(seg.end)}]  ")
        ts_run.bold = True
        ts_run.font.size = Pt(9)
        ts_run.font.color.rgb = RGBColor(100, 100, 100)
        text_run = p.add_run(seg.text.strip())
        text_run.font.size = Pt(11)

    export_name = f"{Path(original_filename).stem}_transcription.docx"
    export_path = EXPORTS_DIR / export_name
    doc.save(str(export_path))
    return export_path
