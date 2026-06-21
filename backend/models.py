from pydantic import BaseModel


class FileInfo(BaseModel):
    id: str
    name: str
    size: int
    type: str  # "upload" or "recording"
    has_transcription: bool = False


class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResult(BaseModel):
    file_id: str
    text: str
    segments: list[TranscriptionSegment]
    model: str
    language: str
    engine: str = ""  # engine that produced this transcript: "whisper" or "voxtral"
    edited: bool = False  # True once the user has manually edited the transcript


class JobStatus(BaseModel):
    job_id: str
    file_id: str
    status: str  # pending, processing, completed, error
    progress: int = 0
    error: str | None = None


class Settings(BaseModel):
    model: str = "base"  # Whisper model size
    transcription_engine: str = "whisper"  # "whisper" (local) or "voxtral" (cloud)
