"""Text-to-speech using gTTS and pyttsx3."""

import logging
import os
import tempfile
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def text_to_speech(
    text: str,
    output_path: Optional[str] = None,
    engine: str = "gtts",
    language: str = "en",
    slow: bool = False,
) -> str:
    """Convert text to speech and save as audio file.
    
    Args:
        text: Text to convert to speech.
        output_path: Path to save audio file. If None, creates a temp file.
        engine: TTS engine to use ('gtts' or 'pyttsx3').
        language: Language code for gTTS.
        slow: Whether to speak slowly (gTTS only).
        
    Returns:
        Path to the generated audio file.
    """
    if not text.strip():
        raise ValueError("Text cannot be empty")

    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3" if engine == "gtts" else ".wav")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    if engine == "gtts":
        return _gtts_speak(text, output_path, language, slow)
    elif engine == "pyttsx3":
        return _pyttsx3_speak(text, output_path)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")


def _gtts_speak(text: str, output_path: str, language: str, slow: bool) -> str:
    """Generate speech using Google Text-to-Speech."""
    try:
        from gtts import gTTS
    except ImportError:
        raise ImportError("gTTS not installed. Install with: pip install gTTS")

    tts = gTTS(text=text, lang=language, slow=slow)
    tts.save(output_path)
    logger.info(f"Generated TTS audio: {output_path}")
    return output_path


def _pyttsx3_speak(text: str, output_path: str) -> str:
    """Generate speech using pyttsx3 (offline)."""
    try:
        import pyttsx3
    except ImportError:
        raise ImportError("pyttsx3 not installed. Install with: pip install pyttsx3")

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    logger.info(f"Generated TTS audio: {output_path}")
    return output_path


def speak_text(text: str, engine: str = "gtts", language: str = "en") -> None:
    """Speak text directly (plays audio).
    
    Args:
        text: Text to speak.
        engine: TTS engine to use.
        language: Language code.
    """
    if engine == "pyttsx3":
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.setProperty("rate", 150)
            eng.say(text)
            eng.runAndWait()
        except ImportError:
            logger.warning("pyttsx3 not available, falling back to gTTS file playback")
            path = text_to_speech(text, engine="gtts", language=language)
            _play_audio(path)
            os.unlink(path)
    else:
        path = text_to_speech(text, engine="gtts", language=language)
        _play_audio(path)
        try:
            os.unlink(path)
        except OSError:
            pass


def _play_audio(path: str) -> None:
    """Play an audio file using the system default player."""
    import platform
    system = platform.system()
    try:
        if system == "Darwin":
            os.system(f'afplay "{path}"')
        elif system == "Linux":
            os.system(f'aplay "{path}" 2>/dev/null || paplay "{path}" 2>/dev/null || play "{path}" 2>/dev/null')
        elif system == "Windows":
            os.system(f'start /wait "" "{path}"')
    except Exception as e:
        logger.warning(f"Could not play audio: {e}")
