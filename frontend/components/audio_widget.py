"""Audio recording and playback component for Streamlit."""

import streamlit as st
import os
import tempfile
from typing import Optional, Dict, Any


def show_recorder(key: str = "audio_recorder") -> Optional[Dict[str, Any]]:
    """Display an audio recorder widget.
    
    Args:
        key: Unique key for the Streamlit widget.
        
    Returns:
        Dictionary with audio_path and transcribed text, or None.
    """
    st.markdown("🎙️ Record your answer:")
    audio_bytes = st.audio_input("Record your answer", key=key)

    if audio_bytes:
        # Save recorded audio
        from app.config import RECORDINGS_DIR
        import hashlib
        audio_hash = hashlib.md5(audio_bytes.getvalue()).hexdigest()[:8]
        audio_path = str(RECORDINGS_DIR / f"answer_{key}_{audio_hash}.wav")

        with open(audio_path, "wb") as f:
            f.write(audio_bytes.getbuffer())

        st.audio(audio_bytes, format="audio/wav")

        # Transcribe
        if st.button("📝 Transcribe", key=f"transcribe_{key}"):
            with st.spinner("Transcribing..."):
                try:
                    from modules.voice.speech_to_text import transcribe_audio
                    result = transcribe_audio(audio_path)
                    text = result.get("text", "")

                    if text:
                        st.success("Transcription complete!")
                        st.text_area("Transcribed text:", value=text, height=100,
                                    key=f"transcription_{key}")

                        return {
                            "audio_path": audio_path,
                            "text": text,
                            "duration": result.get("duration", 0),
                        }
                    else:
                        st.warning("No speech detected. Please try again.")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

    return None


def show_audio_player(audio_path: str, label: str = "Audio") -> None:
    """Display an audio player for a file.
    
    Args:
        audio_path: Path to the audio file.
        label: Label for the player.
    """
    if os.path.exists(audio_path):
        st.audio(audio_path, format="audio/wav")
    else:
        st.warning(f"Audio file not found: {label}")


def show_tts_button(text: str, key: str = "tts") -> Optional[str]:
    """Display a button that plays text as speech.
    
    Args:
        text: Text to speak.
        key: Unique key for the button.
        
    Returns:
        Path to generated audio file, or None.
    """
    if st.button("🔊", key=key):
        try:
            from modules.voice.text_to_speech import text_to_speech
            from app.config import RECORDINGS_DIR
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            audio_path = str(RECORDINGS_DIR / f"tts_{text_hash}.mp3")
            text_to_speech(text, output_path=audio_path)
            st.audio(audio_path)
            return audio_path
        except Exception as e:
            st.warning(f"TTS failed: {e}")
    return None
