import json
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import SETTINGS_FILE, DEFAULT_MODEL, WHISPER_MODELS
from models import Settings
from routers import files, transcribe, export, refine
from services.settings_service import set_settings as save_settings_to_cache, get_settings as load_settings_from_cache

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
app.include_router(refine.router)


def _load_settings() -> Settings:
    """Load settings from file or return defaults.
    
    Returns:
        Settings object with current configuration
    """
    return load_settings_from_cache()


def _save_settings(settings: Settings):
    """Save settings to file and update in-memory state.
    
    Args:
        settings: Settings object to save
    """
    SETTINGS_FILE.write_text(settings.model_dump_json(indent=2))
    save_settings_to_cache(settings)


@app.get("/api/settings", response_model=Settings)
async def get_settings() -> Settings:
    """Get current settings.
    
    Returns:
        Current Settings object
    """
    return _load_settings()


@app.put("/api/settings", response_model=Settings)
async def update_settings(settings: Settings) -> Settings:
    """Update settings.
    
    Args:
        settings: Settings object with updated values
        
    Returns:
        Updated Settings object
    """
    if settings.model not in WHISPER_MODELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {WHISPER_MODELS}")
    _save_settings(settings)
    return settings


@app.get("/api/health")
async def health():
    return {"status": "ok"}
