"""Mistral API client service.

Handles all communication with Mistral's API, including:
- Authentication via API key
- Chat completions for text refinement
- Error handling and retry logic
- Configuration management

Environment Variables:
    MISTRAL_API_KEY: Mistral API key (primary method)
"""

import os
from typing import Optional, Dict, List

from mistralai.client import Mistral


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
            api_key: Mistral API key. If not provided, will be read from environment.
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.client = None
        self._initialize_client()
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variables.
        
        Returns:
            API key string or None if not found
        """
        return os.environ.get("MISTRAL_API_KEY")
    
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
            error_str = str(e).lower()

            # Classify the error so the UI can show a clear, actionable message.
            if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                raise MistralRateLimitError(f"Mistral API rate limit exceeded: {e}")
            elif "401" in error_str or "403" in error_str or "unauthorized" in error_str \
                    or "authentication" in error_str or "api key" in error_str:
                raise MistralAuthenticationError(f"Mistral API authentication failed (check your API key): {e}")
            elif "timeout" in error_str or "timed out" in error_str:
                raise MistralNetworkError(f"Mistral API request timed out: {e}")
            else:
                raise MistralNetworkError(f"Mistral API error: {e}")
    
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


def set_mistral_api_key(api_key: str) -> None:
    """Set Mistral API key and reset client.
    
    Args:
        api_key: New API key
    """
    global _mistral_client
    _mistral_client = MistralClientService(api_key=api_key)