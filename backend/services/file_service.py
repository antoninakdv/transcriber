import json
import uuid
from pathlib import Path

from config import UPLOADS_DIR, RECORDINGS_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from models import FileInfo, TranscriptionResult

_MAX_MB = MAX_UPLOAD_BYTES // (1024 * 1024)


def generate_id() -> str:
    return uuid.uuid4().hex[:12]


def get_file_dir(file_type: str) -> Path:
    return UPLOADS_DIR if file_type == "upload" else RECORDINGS_DIR


def save_upload(filename: str, content: bytes) -> FileInfo:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File too large (max {_MAX_MB} MB)")
    # The file is written under a generated id + validated extension, so the client
    # filename can never influence the path on disk; we keep only its bare name for display.
    file_id = generate_id()
    safe_name = f"{file_id}{ext}"
    path = UPLOADS_DIR / safe_name
    path.write_bytes(content)
    meta = FileInfo(
        id=file_id,
        name=Path(filename).name,
        size=len(content),
        type="upload",
        has_transcription=False,
    )
    _save_meta(file_id, meta, "upload")
    return meta


def save_recording(content: bytes, filename: str = "recording.webm") -> FileInfo:
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Recording too large (max {_MAX_MB} MB)")
    file_id = generate_id()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".webm"
    safe_name = f"{file_id}{ext}"
    path = RECORDINGS_DIR / safe_name
    path.write_bytes(content)
    meta = FileInfo(
        id=file_id,
        name=Path(filename).name,
        size=len(content),
        type="recording",
        has_transcription=False,
    )
    _save_meta(file_id, meta, "recording")
    return meta


def list_files() -> list[FileInfo]:
    files = []
    for dir_path, file_type in [(UPLOADS_DIR, "upload"), (RECORDINGS_DIR, "recording")]:
        for meta_path in dir_path.glob("*.meta.json"):
            try:
                data = json.loads(meta_path.read_text())
                file_id = data["id"]
                data["has_transcription"] = _transcription_path(file_id, file_type).exists()
                files.append(FileInfo(**data))
            except Exception:
                continue
    return files


def get_file_path(file_id: str) -> Path | None:
    for dir_path in [UPLOADS_DIR, RECORDINGS_DIR]:
        for p in dir_path.iterdir():
            if p.stem == file_id and not p.name.endswith(".meta.json") and not p.name.endswith(".transcription.json"):
                return p
    return None


def get_file_info(file_id: str) -> FileInfo | None:
    for dir_path in [UPLOADS_DIR, RECORDINGS_DIR]:
        meta_path = dir_path / f"{file_id}.meta.json"
        if meta_path.exists():
            data = json.loads(meta_path.read_text())
            file_type = data.get("type", "upload")
            data["has_transcription"] = _transcription_path(file_id, file_type).exists()
            return FileInfo(**data)
    return None


def delete_file(file_id: str) -> bool:
    deleted = False
    for dir_path in [UPLOADS_DIR, RECORDINGS_DIR]:
        for p in list(dir_path.iterdir()):
            if p.stem == file_id or p.name.startswith(f"{file_id}."):
                p.unlink()
                deleted = True
    return deleted


def save_transcription(file_id: str, result: TranscriptionResult):
    info = get_file_info(file_id)
    file_type = info.type if info else "upload"
    dir_path = get_file_dir(file_type)
    path = dir_path / f"{file_id}.transcription.json"
    path.write_text(result.model_dump_json(indent=2))


def get_transcription(file_id: str) -> TranscriptionResult | None:
    for dir_path in [UPLOADS_DIR, RECORDINGS_DIR]:
        path = dir_path / f"{file_id}.transcription.json"
        if path.exists():
            return TranscriptionResult(**json.loads(path.read_text()))
    return None


def _save_meta(file_id: str, meta: FileInfo, file_type: str):
    dir_path = get_file_dir(file_type)
    path = dir_path / f"{file_id}.meta.json"
    path.write_text(meta.model_dump_json(indent=2))


def _transcription_path(file_id: str, file_type: str) -> Path:
    return get_file_dir(file_type) / f"{file_id}.transcription.json"
