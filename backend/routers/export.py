from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services import file_service
from services.docx_service import generate_docx

router = APIRouter(prefix="/api/export", tags=["export"])


class RefinedExportRequest(BaseModel):
    """Request body for exporting a refined transcript to DOCX."""
    refined_text: str
    refined_mode: str


@router.post("/docx/{file_id}")
async def export_docx(file_id: str, refined_mode: str = None):
    """Export transcription to DOCX.
    
    Args:
        file_id: ID of the file to export
        refined_mode: Optional mode name if exporting refined transcript
        
    Returns:
        FileResponse with the DOCX file
    """
    transcription = file_service.get_transcription(file_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="No transcription found for this file")

    info = file_service.get_file_info(file_id)
    original_name = info.name if info else f"{file_id}.audio"

    # Check if we need to export refined version
    refined_text = None
    if refined_mode:
        # For now, refined text is stored in the frontend, but in future we might
        # store it in the backend. For M2, we'll just export the original.
        # This is a placeholder for future refinement persistence.
        pass

    path = generate_docx(transcription, original_name, refined_text, refined_mode)
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@router.post("/docx/refined/{file_id}")
async def export_refined_docx(file_id: str, req: RefinedExportRequest):
    """Export a refined transcript to DOCX.

    The refined text is sent in the JSON body (it can be long), alongside the name
    of the refinement mode used.
    """
    transcription = file_service.get_transcription(file_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="No transcription found for this file")

    info = file_service.get_file_info(file_id)
    original_name = info.name if info else f"{file_id}.audio"

    path = generate_docx(transcription, original_name, req.refined_text, req.refined_mode)
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )
