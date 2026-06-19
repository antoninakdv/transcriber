from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
UPLOADS_DIR = WORKSPACE_DIR / "uploads"
RECORDINGS_DIR = WORKSPACE_DIR / "recordings"
EXPORTS_DIR = WORKSPACE_DIR / "exports"

for d in [UPLOADS_DIR, RECORDINGS_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".ogg", ".mp3", ".wav", ".mp4", ".m4a", ".webm", ".flac", ".aac"}

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_MODEL = "base"

SETTINGS_FILE = BASE_DIR / "settings.json"
