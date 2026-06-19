import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from models import JobStatus, TranscriptionResult, TranscriptionSegment
from services import file_service, whisper_service

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])

jobs: dict[str, JobStatus] = {}
executor = ThreadPoolExecutor(max_workers=1)


def _run_transcription(job_id: str, file_id: str, audio_path: str, model: str):
    try:
        jobs[job_id].status = "processing"
        jobs[job_id].progress = 10
        result = whisper_service.transcribe(audio_path, model)
        jobs[job_id].progress = 90

        segments = [
            TranscriptionSegment(start=s["start"], end=s["end"], text=s["text"])
            for s in result.get("segments", [])
        ]
        transcription = TranscriptionResult(
            file_id=file_id,
            text=result.get("text", ""),
            segments=segments,
            model=model,
            language="en",
        )
        file_service.save_transcription(file_id, transcription)
        jobs[job_id].status = "completed"
        jobs[job_id].progress = 100
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)


@router.post("/{file_id}")
async def start_transcription(file_id: str, model: str = ""):
    file_path = file_service.get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    if not model:
        from config import DEFAULT_MODEL
        model = DEFAULT_MODEL

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = JobStatus(job_id=job_id, file_id=file_id, status="pending", progress=0)
    executor.submit(_run_transcription, job_id, file_id, str(file_path), model)
    return {"job_id": job_id}


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@router.get("/{file_id}/result", response_model=TranscriptionResult)
async def get_result(file_id: str):
    result = file_service.get_transcription(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return result
