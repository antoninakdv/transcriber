"""Mistral API client service.

Single source of truth for the Mistral API key and all calls to Mistral's API
(text refinement and Voxtral speech-to-text).

Key resolution precedence (see get_active_key):
    1. MISTRAL_API_KEY environment variable / .env  (primary, headless-friendly)
    2. A key entered this session via the Settings UI (held in memory only)
    3. A key the user chose to "remember", stored in the OS keychain (keyring)

The raw key is never logged, echoed, or written to a plaintext file.
"""

import os
from typing import Optional, Dict, List

import keyring
from mistralai.client import Mistral

# OS keychain coordinates for a "remembered" key (Windows Credential Manager, etc.).
_KEYRING_SERVICE = "whisper-transcriber"
_KEYRING_USERNAME = "mistral_api_key"

# Key entered via the Settings UI for this process only (never persisted to disk).
_session_key: Optional[str] = None


def _get_remembered_key() -> Optional[str]:
    """Read a remembered key from the OS keychain, or None if absent/unavailable."""
    try:
        return keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        # A missing or unavailable keychain backend must never break the app.
        return None


def get_active_key() -> Optional[str]:
    """Resolve the active Mistral API key by precedence, or None if unset."""
    return os.environ.get("MISTRAL_API_KEY") or _session_key or _get_remembered_key()


def _key_source() -> Optional[str]:
    """Name where the active key came from: 'environment', 'session', 'keychain', or None."""
    if os.environ.get("MISTRAL_API_KEY"):
        return "environment"
    if _session_key:
        return "session"
    if _get_remembered_key():
        return "keychain"
    return None


def set_key(api_key: str, remember: bool = False) -> None:
    """Store a key entered via the UI for this session, optionally in the OS keychain.

    Args:
        api_key: The Mistral API key to use.
        remember: If True, also save it to the OS keychain so it survives restarts.
    """
    global _session_key
    _session_key = api_key
    if remember:
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, api_key)
    reset_mistral_client()


def clear_key() -> None:
    """Forget the session key and remove any remembered key from the OS keychain."""
    global _session_key
    _session_key = None
    try:
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        # No remembered key to delete (or no backend) — nothing to do.
        pass
    reset_mistral_client()


def key_status() -> Dict[str, object]:
    """Describe key configuration for the UI without ever exposing the raw key.

    Returns:
        Dict with `configured` (bool), `source` (str or None) and `hint` (last 4
        characters, or None) — safe to send to the browser.
    """
    key = get_active_key()
    return {
        "configured": bool(key),
        "source": _key_source(),
        "hint": key[-4:] if key else None,
    }


class MistralClientError(Exception):
    """Base exception for Mistral client errors."""
    pass


class MistralAuthenticationError(MistralClientError):
    """Raised when Mistral API authentication fails."""
    pass


class MistralRateLimitError(MistralClientError):
    """Raised when Mistral API rate limits are exceeded."""
    pass


class MistralNetworkError(MistralClientError):
    """Raised when there are network issues with Mistral API."""
    pass


class MistralClientService:
    """Service for interacting with Mistral API.
    
    This service provides a clean interface for making calls to Mistral's API
    with proper error handling, configuration, and graceful degradation when
    no API key is available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Mistral client service.

        Args:
            api_key: Mistral API key. If not provided, the active key is resolved
                from env / session / keychain (see get_active_key).
        """
        self.api_key = api_key or get_active_key()
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Mistral client if API key is available."""
        if self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
            except Exception as e:
                raise MistralAuthenticationError(f"Failed to initialize Mistral client: {e}")
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Mistral API is available (key configured and client initialized).
        
        Returns:
            True if Mistral API can be used, False otherwise
        """
        return self.client is not None and self.api_key is not None
    
    def refine_text(
        self,
        transcript: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        model: str = "mistral-small-latest",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        timeout: float = 30.0
    ) -> str:
        """Refine text using Mistral's chat completion API.
        
        Args:
            transcript: The transcript text to refine
            system_prompt: System prompt defining the refinement task
            user_prompt: Optional user prompt. If not provided, transcript is used as user message.
            model: Mistral model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            
        Returns:
            Refined text from Mistral API
            
        Raises:
            MistralAuthenticationError: If API key is not configured
            MistralRateLimitError: If rate limit is exceeded
            MistralNetworkError: If there are network issues
            MistralClientError: For other Mistral API errors
        """
        if not self.is_available():
            raise MistralAuthenticationError(
                "Mistral API is not available. Please set MISTRAL_API_KEY environment variable."
            )
        
        if not transcript:
            return ""
        
        # Prepare messages as list of dict objects (simpler approach)
        messages: List[Dict[str, str]] = []
        
        # Add system message
        messages.append({"role": "system", "content": system_prompt})
        
        # Add user message with transcript
        user_content = user_prompt or transcript
        messages.append({"role": "user", "content": user_content})
        
        try:
            # In the mistralai SDK, chat completions are made via chat.complete().
            # The request timeout is passed in milliseconds (timeout_ms).
            response = self.client.chat.complete(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_ms=int(timeout * 1000),
            )

            # Extract and return the content from the first choice
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            else:
                return ""
                
        except Exception as e:
            # Map to a typed, user-readable error so the UI can react sensibly.
            raise self._classify_error(e)
    
    def transcribe_audio(
        self,
        audio_path: str,
        filename: str,
        model: str = "voxtral-mini-latest",
        language: Optional[str] = None,
        timeout: float = 300.0,
    ) -> Dict[str, object]:
        """Transcribe an audio file with Mistral's Voxtral speech-to-text API.

        Args:
            audio_path: Path to the audio file on disk.
            filename: Original file name (helps the API detect the format).
            model: Voxtral transcription model id.
            language: Optional ISO language hint; omitted means auto-detect.
            timeout: Request timeout in seconds (audio can take a while).

        Returns:
            Normalized dict with `text`, `language` and `segments`
            (each `{start, end, text}`) — the same shape the Whisper path produces.

        Raises:
            MistralAuthenticationError / MistralRateLimitError / MistralNetworkError
        """
        if not self.is_available():
            raise MistralAuthenticationError(
                "Mistral API is not available. Configure a Mistral API key to use Voxtral."
            )

        try:
            with open(audio_path, "rb") as f:
                response = self.client.audio.transcriptions.complete(
                    model=model,
                    file={"content": f, "file_name": filename},
                    language=language,
                    timestamp_granularities=["segment"],
                    timeout_ms=int(timeout * 1000),
                )
        except Exception as e:
            raise self._classify_error(e)

        segments = [
            {"start": s.start or 0.0, "end": s.end or 0.0, "text": s.text or ""}
            for s in (response.segments or [])
        ]
        return {
            "text": response.text or "",
            "language": response.language or (language or ""),
            "segments": segments,
        }

    def test_connection(self) -> tuple[bool, str]:
        """Validate the active key with one lightweight call.

        Returns:
            (ok, message) — never includes the key itself.
        """
        if not self.is_available():
            return False, "No Mistral API key configured."
        try:
            self.client.models.list()
            return True, "Connection successful. Mistral API key is valid."
        except Exception as e:
            return False, str(self._classify_error(e))

    @staticmethod
    def _classify_error(e: Exception) -> MistralClientError:
        """Map a raw SDK/network error to a typed, user-readable Mistral error."""
        error_str = str(e).lower()
        if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
            return MistralRateLimitError(f"Mistral API rate limit exceeded: {e}")
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str \
                or "authentication" in error_str or "api key" in error_str:
            return MistralAuthenticationError(f"Mistral API authentication failed (check your API key): {e}")
        if "timeout" in error_str or "timed out" in error_str:
            return MistralNetworkError(f"Mistral API request timed out: {e}")
        return MistralNetworkError(f"Mistral API error: {e}")

    def get_available_models(self) -> List[str]:
        """Get list of available Mistral models.

        Returns:
            List of available model names

        Raises:
            MistralClientError: If models cannot be retrieved
        """
        if not self.is_available():
            return []

        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            raise MistralClientError(f"Failed to retrieve available models: {e}")


# Module-level singleton instance
_mistral_client: Optional[MistralClientService] = None


def get_mistral_client() -> MistralClientService:
    """Get the singleton Mistral client service instance.
    
    Returns:
        MistralClientService instance
    """
    global _mistral_client
    if _mistral_client is None:
        _mistral_client = MistralClientService()
    return _mistral_client


def reset_mistral_client() -> None:
    """Reset the singleton Mistral client service instance.
    
    Useful for testing or when API key changes.
    """
    global _mistral_client
    _mistral_client = None


