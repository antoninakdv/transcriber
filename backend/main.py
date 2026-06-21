from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import SETTINGS_FILE, WHISPER_MODELS
from models import Settings
from routers import files, transcribe, export, refine
from services.settings_service import set_settings as save_settings_to_cache, get_settings as load_settings_from_cache
from services import mistral_client

TRANSCRIPTION_ENGINES = ["whisper", "voxtral"]

app = FastAPI(title="Transcription API")

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


class MistralKeyRequest(BaseModel):
    """Body for saving a Mistral API key from the Settings UI."""
    api_key: str
    remember: bool = False


def _settings_payload() -> dict:
    """Build the settings response: app settings plus Mistral key status.

    Never includes the raw key — only whether one is set, its source, and a last-4
    hint (see mistral_client.key_status).
    """
    settings = _load_settings()
    return {
        "model": settings.model,
        "transcription_engine": settings.transcription_engine,
        "mistral": mistral_client.key_status(),
    }


@app.get("/api/settings")
async def get_settings() -> dict:
    """Get current settings plus Mistral connection status (no raw key)."""
    return _settings_payload()


@app.put("/api/settings")
async def update_settings(settings: Settings) -> dict:
    """Update the model and transcription-engine settings."""
    if settings.model not in WHISPER_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {WHISPER_MODELS}")
    if settings.transcription_engine not in TRANSCRIPTION_ENGINES:
        raise HTTPException(status_code=400, detail=f"Invalid engine. Choose from: {TRANSCRIPTION_ENGINES}")
    _save_settings(settings)
    return _settings_payload()


@app.post("/api/settings/mistral-key")
async def save_mistral_key(req: MistralKeyRequest) -> dict:
    """Save a Mistral API key for this session (optionally remember in the OS keychain).

    The key is held in memory / the OS keychain only — never written to settings.json
    or any plaintext file, and never returned to the browser.
    """
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    mistral_client.set_key(req.api_key.strip(), remember=req.remember)
    return mistral_client.key_status()


@app.delete("/api/settings/mistral-key")
async def delete_mistral_key() -> dict:
    """Forget the session key and remove any remembered key from the OS keychain."""
    mistral_client.clear_key()
    return mistral_client.key_status()


@app.post("/api/settings/test-connection")
async def test_mistral_connection() -> dict:
    """Validate the active key with one lightweight Mistral call."""
    ok, message = mistral_client.get_mistral_client().test_connection()
    return {"ok": ok, "message": message}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
