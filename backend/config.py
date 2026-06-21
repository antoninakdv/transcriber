import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from a local .env file into the environment.

    A tiny, dependency-free reader so a gitignored `.env` works as the primary way
    to supply secrets like MISTRAL_API_KEY (keeping us to a single new dependency).
    A value already set in the real environment always wins, so an explicitly
    exported variable is never overridden. Looks in the backend folder first, then
    the repository root.
    """
    for env_path in (BASE_DIR / ".env", REPO_ROOT / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

WORKSPACE_DIR = BASE_DIR / "workspace"
UPLOADS_DIR = WORKSPACE_DIR / "uploads"
RECORDINGS_DIR = WORKSPACE_DIR / "recordings"
EXPORTS_DIR = WORKSPACE_DIR / "exports"

for d in [UPLOADS_DIR, RECORDINGS_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".ogg", ".mp3", ".wav", ".mp4", ".m4a", ".webm", ".flac", ".aac"}

# Server-side cap on uploaded/recorded audio size (defence in depth, not just the UI).
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_MODEL = "base"

SETTINGS_FILE = BASE_DIR / "settings.json"
