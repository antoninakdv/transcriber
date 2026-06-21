"""Settings service - provides access to application settings without circular imports."""

from config import DEFAULT_MODEL, SETTINGS_FILE
from models import Settings

# Module-level cache for settings
_current_settings: Settings | None = None


def get_settings() -> Settings:
    """Get current settings, loading from file if not already loaded.
    
    Returns:
        Current Settings object
    """
    global _current_settings
    if _current_settings is None:
        if SETTINGS_FILE.exists():
            import json
            data = json.loads(SETTINGS_FILE.read_text())
            _current_settings = Settings(**data)
        else:
            _current_settings = Settings(model=DEFAULT_MODEL)
    return _current_settings


def set_settings(settings: Settings) -> None:
    """Update current settings in memory.
    
    Args:
        settings: Settings object to cache
    """
    global _current_settings
    _current_settings = settings


def get_default_model() -> str:
    """Get the current default model from settings or config default.
    
    Returns:
        Model name string
    """
    settings = get_settings()
    return settings.model