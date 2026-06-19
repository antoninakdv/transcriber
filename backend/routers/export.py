from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services import file_service
from services.docx_service import generate_docx

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/docx/{file_id}")
async def export_docx(file_id: str):
    transcription = file_service.get_transcription(file_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="No transcription found for this file")

    info = file_service.get_file_info(file_id)
    original_name = info.name if info else f"{file_id}.audio"

    path = generate_docx(transcription, original_name)
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )
