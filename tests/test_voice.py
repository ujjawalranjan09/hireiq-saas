"""Tests for the voice module."""

import unittest
import tempfile
import os


class TestTextToSpeech(unittest.TestCase):
    """Test TTS functionality."""

    def test_text_to_speech_gtts(self):
        """Test gTTS generation."""
        try:
            from modules.voice.text_to_speech import text_to_speech
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                path = f.name
            try:
                result = text_to_speech("Hello, this is a test.", output_path=path, engine="gtts")
                self.assertEqual(result, path)
                self.assertTrue(os.path.exists(path))
                self.assertGreater(os.path.getsize(path), 0)
            finally:
                if os.path.exists(path):
                    os.unlink(path)
        except ImportError:
            self.skipTest("gTTS not installed")

    def test_text_to_speech_empty(self):
        """Test TTS with empty text."""
        from modules.voice.text_to_speech import text_to_speech
        with self.assertRaises(ValueError):
            text_to_speech("")


class TestSpeechToText(unittest.TestCase):
    """Test speech-to-text functionality."""

    def test_transcribe_nonexistent_file(self):
        """Test transcription with missing file."""
        from modules.voice.speech_to_text import transcribe_audio
        with self.assertRaises(FileNotFoundError):
            transcribe_audio("/nonexistent/path.wav")


class TestVoiceEmotion(unittest.TestCase):
    """Test voice emotion analysis."""

    def test_analyze_nonexistent_file(self):
        """Test with missing file."""
        from modules.voice.voice_emotion import analyze_voice_emotion
        with self.assertRaises(FileNotFoundError):
            analyze_voice_emotion("/nonexistent/path.wav")

    def test_default_voice_features(self):
        """Test default features."""
        from modules.voice.voice_emotion import _default_voice_features
        features = _default_voice_features()
        self.assertIn("pitch_mean", features)
        self.assertIn("confidence_score", features)
        self.assertIn("emotion_label", features)


if __name__ == "__main__":
    unittest.main()
