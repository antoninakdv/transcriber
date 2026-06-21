from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from models import FileInfo
from services import file_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileInfo)
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return file_service.save_upload(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recording", response_model=FileInfo)
async def save_recording(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return file_service.save_recording(content, file.filename or "recording.webm")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[FileInfo])
async def list_files():
    return file_service.list_files()


@router.get("/{file_id}/audio")
async def serve_audio(file_id: str):
    path = file_service.get_file_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="audio/ogg")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    if not file_service.delete_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted"}
