import whisper

_MODEL_CACHE: dict[str, object] = {}

def _get_model(name: str):
    if name not in _MODEL_CACHE:
        _MODEL_CACHE[name] = whisper.load_model(name)
    return _MODEL_CACHE[name]

def transcribe(audio_path: str, *, model_name: str = "base") -> list[dict]:
    print(f"[whisper] Transcribing: {audio_path} (model={model_name})")
    model = _get_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True)
    print("[whisper] Transcription complete")
    return result["segments"]