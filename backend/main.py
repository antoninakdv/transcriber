import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import SETTINGS_FILE, DEFAULT_MODEL, WHISPER_MODELS
from models import Settings
from routers import files, transcribe, export

app = FastAPI(title="Whisper Transcription API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(transcribe.router)
app.include_router(export.router)


def _load_settings() -> Settings:
    if SETTINGS_FILE.exists():
        data = json.loads(SETTINGS_FILE.read_text())
        return Settings(**data)
    return Settings(model=DEFAULT_MODEL)


def _save_settings(settings: Settings):
    SETTINGS_FILE.write_text(settings.model_dump_json(indent=2))


@app.get("/api/settings", response_model=Settings)
async def get_settings():
    return _load_settings()


@app.put("/api/settings", response_model=Settings)
async def update_settings(settings: Settings):
    if settings.model not in WHISPER_MODELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {WHISPER_MODELS}")
    _save_settings(settings)
    import config
    config.DEFAULT_MODEL = settings.model
    return settings


@app.get("/api/health")
async def health():
    return {"status": "ok"}
