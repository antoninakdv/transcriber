import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from models import JobStatus, TranscriptionResult, TranscriptionSegment
from services import file_service
from services.transcription_engines import get_engine
from services.mistral_client import get_mistral_client

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


def _run_transcription(
    job_id: str,
    file_id: str,
    audio_path: str,
    filename: str,
    engine_name: str,
    whisper_model: str,
    jobs: Dict[str, JobStatus],
):
    """Run transcription in a background thread using the selected engine.

    Args:
        job_id: Unique identifier for the transcription job
        file_id: File identifier being transcribed
        audio_path: Path to audio file
        filename: Original file name (used by the Voxtral API for format detection)
        engine_name: "whisper" (local) or "voxtral" (cloud)
        whisper_model: Whisper model name (ignored by the Voxtral engine)
        jobs: Dictionary to store job state
    """
    engine = get_engine(engine_name, whisper_model)
    # Visible in the backend terminal while a job runs.
    print(f"Transcribing {job_id} with engine={engine_name} model={engine.model_name}", flush=True)
    try:
        jobs[job_id].status = "processing"
        jobs[job_id].progress = 10

        result = engine.transcribe(audio_path, filename)
        jobs[job_id].progress = 90

        segments = [
            TranscriptionSegment(start=s["start"], end=s["end"], text=s["text"])
            for s in result.get("segments", [])
        ]
        transcription = TranscriptionResult(
            file_id=file_id,
            text=result.get("text", ""),
            segments=segments,
            model=result.get("model", engine.model_name),
            language=result.get("language", "en"),
            engine=engine_name,  # record the engine that actually produced this transcript
        )
        file_service.save_transcription(file_id, transcription)
        jobs[job_id].status = "completed"
        jobs[job_id].progress = 100
        print(f"Transcribed {job_id} with engine={engine_name} model={transcription.model}", flush=True)
    except Exception as e:
        # No silent fallback: a Voxtral failure fails the job with a clear reason
        # rather than quietly transcribing with Whisper instead.
        jobs[job_id].status = "error"
        if engine_name == "voxtral":
            jobs[job_id].error = f"Voxtral transcription failed (no fallback to Whisper): {e}"
        else:
            jobs[job_id].error = str(e)
        print(f"Transcription {job_id} FAILED (engine={engine_name}): {e}", flush=True)


@router.post("/{file_id}")
async def start_transcription(
    file_id: str,
    model: str = "",
    engine: str = "",
    jobs: Dict[str, JobStatus] = Depends(get_jobs),
):
    """Start a transcription job for the given file.

    Args:
        file_id: ID of the file to transcribe
        model: Whisper model to use (optional, defaults to configured default)
        engine: Engine override "whisper"/"voxtral" (optional, defaults to settings)
        jobs: Jobs dictionary (injected via dependency injection)

    Returns:
        JSON with job_id for status tracking
    """
    file_path = file_service.get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    from services.settings_service import get_default_model, get_settings
    if not model:
        model = get_default_model()
    if not engine:
        engine = get_settings().transcription_engine

    # Voxtral is cloud-only and requires a configured key; fail clearly and keep
    # Whisper available rather than starting a job that can only error.
    if engine == "voxtral" and not get_mistral_client().is_available():
        raise HTTPException(
            status_code=400,
            detail="Voxtral needs a Mistral API key. Add one in Settings or use the Whisper engine.",
        )

    info = file_service.get_file_info(file_id)
    filename = info.name if info else Path(str(file_path)).name

    # Prune finished jobs from previous runs here, not during status polling, so a
    # just-completed job is never deleted before the client reads its final status.
    cleanup_completed_jobs(jobs)

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = JobStatus(job_id=job_id, file_id=file_id, status="pending", progress=0)
    _executor.submit(
        _run_transcription, job_id, file_id, str(file_path), filename, engine, model, jobs
    )
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


class TranscriptUpdate(BaseModel):
    """Body for a manual transcript edit."""
    text: str


@router.put("/{file_id}/result", response_model=TranscriptionResult)
async def update_result(file_id: str, body: TranscriptUpdate):
    """Persist a manually edited transcript as the canonical text for this file.

    The edited text becomes what export and refinement use; segments and metadata
    are kept as-is so the original timing reference is not lost.
    """
    result = file_service.get_transcription(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transcription not found")

    result.text = body.text
    result.edited = True
    file_service.save_transcription(file_id, result)
    return result
