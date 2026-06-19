_model_cache: dict = {}


def _get_whisper():
    try:
        import whisper
        return whisper
    except ImportError:
        raise RuntimeError(
            "Whisper is not installed. Run: pip install openai-whisper"
        )


def load_model(model_name: str):
    whisper = _get_whisper()
    if model_name not in _model_cache:
        _model_cache.clear()
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def transcribe(audio_path: str, model_name: str = "base") -> dict:
    model = load_model(model_name)
    result = model.transcribe(audio_path, language="en")
    return result
