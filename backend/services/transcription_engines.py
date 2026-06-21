"""Pluggable transcription engines.

The app can turn audio into text two ways:
- WhisperEngine: the local, offline default (unchanged behaviour).
- VoxtralEngine: Mistral's cloud speech-to-text (needs an API key).

Both implement the same tiny interface and return the same normalized result, so
nothing downstream (view, .docx export, refinement) needs to know which produced
it. Adding another engine later is one new class plus one line in get_engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from services import whisper_service
from services.mistral_client import get_mistral_client

# A normalized result is a dict: {text, language, segments, model}, where each
# segment is {start, end, text}. Aliased for readable type hints.
Result = Dict[str, object]


class TranscriptionEngine(ABC):
    """Turns an audio file into a normalized transcription result."""

    name: str

    @abstractmethod
    def transcribe(self, audio_path: str, filename: str) -> Result:
        """Transcribe the given audio file into {text, language, segments, model}."""


class WhisperEngine(TranscriptionEngine):
    """Local Whisper transcription — the default, offline path (unchanged)."""

    name = "whisper"

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name

    def transcribe(self, audio_path: str, filename: str) -> Result:
        result = whisper_service.transcribe(audio_path, self.model_name)
        segments: List[Dict[str, object]] = [
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in result.get("segments", [])
        ]
        return {
            "text": result.get("text", ""),
            "language": "en",
            "segments": segments,
            "model": self.model_name,
        }


class VoxtralEngine(TranscriptionEngine):
    """Cloud transcription via Mistral's Voxtral speech-to-text API (needs a key)."""

    name = "voxtral"
    model_name = "voxtral-mini-latest"

    def transcribe(self, audio_path: str, filename: str) -> Result:
        result = get_mistral_client().transcribe_audio(
            audio_path, filename, model=self.model_name
        )
        return {
            "text": result["text"],
            "language": result.get("language") or "",
            "segments": result["segments"],
            "model": self.model_name,
        }


def get_engine(engine: str, whisper_model: str = "base") -> TranscriptionEngine:
    """Select an engine by name; defaults to local Whisper for any unknown value."""
    if engine == "voxtral":
        return VoxtralEngine()
    return WhisperEngine(model_name=whisper_model)
