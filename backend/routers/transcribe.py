import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends

from models import JobStatus, TranscriptionResult, TranscriptionSegment
from services import file_service, whisper_service

# Application state for job tracking
_jobs: Dict[str, JobStatus] = {}
_executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])


def get_jobs() -> Dict[str, JobStatus]:
    """Get the jobs dictionary for dependency injection."""
    return _jobs


def get_executor() -> ThreadPoolExecutor:
    """Get the thread pool executor for dependency injection."""
    return _executor


def cleanup_completed_jobs(jobs: Dict[str, JobStatus]) -> None:
    """Remove completed and failed jobs from memory to prevent memory leaks.
    
    Args:
        jobs: Jobs dictionary to clean up
    """
    completed_job_ids = [
        job_id for job_id, job in jobs.items() 
        if job.status in ("completed", "error")
    ]
    for job_id in completed_job_ids:
        del jobs[job_id]


def _run_transcription(job_id: str, file_id: str, audio_path: str, model: str, jobs: Dict[str, JobStatus]):
    """Run transcription in background thread.
    
    Args:
        job_id: Unique identifier for the transcription job
        file_id: File identifier being transcribed
        audio_path: Path to audio file
        model: Whisper model name
        jobs: Dictionary to store job state
    """
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
async def start_transcription(file_id: str, model: str = "", jobs: Dict[str, JobStatus] = Depends(get_jobs)):
    """Start a transcription job for the given file.
    
    Args:
        file_id: ID of the file to transcribe
        model: Whisper model to use (optional, defaults to configured default)
        jobs: Jobs dictionary (injected via dependency injection)
        
    Returns:
        JSON with job_id for status tracking
    """
    file_path = file_service.get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    if not model:
        from services.settings_service import get_default_model
        model = get_default_model()

    # Prune finished jobs from previous runs here, not during status polling, so a
    # just-completed job is never deleted before the client reads its final status.
    cleanup_completed_jobs(jobs)

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = JobStatus(job_id=job_id, file_id=file_id, status="pending", progress=0)
    _executor.submit(_run_transcription, job_id, file_id, str(file_path), model, jobs)
    return {"job_id": job_id}


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_status(job_id: str, jobs: Dict[str, JobStatus] = Depends(get_jobs)):
    """Get the status of a transcription job.
    
    Args:
        job_id: The job identifier to check
        jobs: Jobs dictionary (injected via dependency injection)
        
    Returns:
        JobStatus with current status, progress, and any error
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@router.get("/{file_id}/result", response_model=TranscriptionResult)
async def get_result(file_id: str):
    result = file_service.get_transcription(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return result
