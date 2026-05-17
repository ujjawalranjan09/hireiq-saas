"""Speech-to-text using OpenAI Whisper."""

import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy-loaded whisper model
_whisper_model = None
_whisper_model_name = None


def _get_whisper_model():
    """Lazily load Whisper model."""
    global _whisper_model, _whisper_model_name
    from app.config import WHISPER_MODEL
    if _whisper_model is None or _whisper_model_name != WHISPER_MODEL:
        try:
            import whisper
            logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
            _whisper_model = whisper.load_model(WHISPER_MODEL)
            _whisper_model_name = WHISPER_MODEL
        except ImportError:
            raise ImportError("openai-whisper not installed. Install with: pip install openai-whisper")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _whisper_model


def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    """Transcribe an audio file to text using Whisper.
    
    Args:
        audio_path: Path to the audio file (WAV, MP3, M4A, etc.)
        
    Returns:
        Dictionary with:
            - text: Transcribed text
            - segments: List of segments with timestamps
            - language: Detected language
            - duration: Audio duration in seconds
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        model = _get_whisper_model()
        result = model.transcribe(audio_path, fp16=False)
        
        logger.info(f"Transcribed audio: {len(result.get('text', ''))} chars, "
                    f"{len(result.get('segments', []))} segments")
        
        return {
            "text": result.get("text", "").strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "en"),
            "duration": _get_audio_duration(audio_path),
        }
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return {
            "text": "",
            "segments": [],
            "language": "en",
            "duration": 0.0,
            "error": str(e),
        }


def transcribe_from_microphone(duration: int = 30, sample_rate: int = 16000) -> Dict[str, Any]:
    """Record from microphone and transcribe.
    
    Args:
        duration: Maximum recording duration in seconds.
        sample_rate: Audio sample rate.
        
    Returns:
        Transcription result dictionary.
    """
    try:
        import sounddevice as sd
        import numpy as np
        import tempfile
        import scipy.io.wavfile as wav
    except ImportError:
        raise ImportError("sounddevice and scipy required for microphone recording")

    logger.info(f"Recording for up to {duration} seconds...")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        wav.write(temp_path, sample_rate, (recording * 32767).astype(np.int16))

    try:
        result = transcribe_audio(temp_path)
        return result
    finally:
        os.unlink(temp_path)


def _get_audio_duration(audio_path: str) -> float:
    """Get audio file duration in seconds."""
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=None)
        return len(y) / sr
    except ImportError:
        # Fallback: try with wave module for WAV files
        try:
            import wave
            with wave.open(audio_path, "r") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0
    except Exception:
        return 0.0
