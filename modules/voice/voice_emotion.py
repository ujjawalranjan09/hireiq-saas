"""Voice emotion analysis using librosa feature extraction."""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def analyze_voice_emotion(audio_path: str) -> Dict[str, Any]:
    """Analyze emotional features from voice audio.
    
    Extracts pitch, speaking speed, pauses, and other acoustic features
    to infer confidence and emotional state.
    
    Args:
        audio_path: Path to the audio file.
        
    Returns:
        Dictionary with voice emotion features:
            - pitch_mean: Average fundamental frequency (Hz)
            - pitch_std: Pitch variation
            - energy_mean: Average energy
            - speaking_rate: Estimated words per minute
            - pause_ratio: Fraction of audio that is silence
            - hesitation_detected: Whether hesitations were detected
            - emotion_label: Inferred emotion
            - confidence_score: Voice confidence score (0-100)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.warning("librosa not available, returning default values")
        return _default_voice_features()

    try:
        y, sr = librosa.load(audio_path, sr=None)

        if len(y) == 0:
            return _default_voice_features()

        # Extract features
        # Pitch (F0) using pyin
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])

        pitch_mean = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_std = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0

        # Energy (RMS)
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_std = float(np.std(rms))

        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_mean = float(np.mean(spectral_centroid))

        # Zero crossing rate (noisiness)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        # Pause detection
        # Normalize RMS to 0-1
        rms_normalized = rms / (np.max(rms) + 1e-8)
        silence_threshold = 0.05
        is_silent = rms_normalized < silence_threshold
        pause_ratio = float(np.mean(is_silent))

        # Hesitation detection: multiple short pauses
        # Find runs of silence
        diff = np.diff(is_silent.astype(int))
        pause_starts = np.where(diff == 1)[0]
        pause_ends = np.where(diff == -1)[0]

        # Short pauses (< 0.5s but > 0.1s) indicate hesitation
        frame_duration = len(y) / sr / len(rms)
        short_pauses = 0
        for start, end in zip(pause_starts, pause_ends):
            duration = (end - start) * frame_duration
            if 0.1 < duration < 0.5:
                short_pauses += 1

        hesitation_detected = short_pauses >= 3

        # Speaking rate estimation
        duration = len(y) / sr
        # Rough estimate: assume average word length and use energy changes
        # A typical English speaker says 120-150 wpm
        # Use voiced segments as proxy
        voiced_ratio = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.5
        estimated_wpm = max(60, min(200, 80 + voiced_ratio * 100))

        # Calculate voice confidence score
        confidence_score = _calculate_voice_confidence(
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            energy_std=energy_std,
            pause_ratio=pause_ratio,
            hesitation_detected=hesitation_detected,
            zcr_mean=zcr_mean,
        )

        # Infer emotion label
        emotion_label = _infer_emotion(
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            pause_ratio=pause_ratio,
        )

        return {
            "pitch_mean": round(pitch_mean, 2),
            "pitch_std": round(pitch_std, 2),
            "energy_mean": round(energy_mean, 6),
            "energy_std": round(energy_std, 6),
            "spectral_centroid": round(spectral_mean, 2),
            "zcr_mean": round(zcr_mean, 6),
            "speaking_speed": round(estimated_wpm, 1),
            "pause_ratio": round(pause_ratio, 3),
            "hesitation_detected": hesitation_detected,
            "short_pauses": short_pauses,
            "emotion_label": emotion_label,
            "confidence_score": round(confidence_score, 1),
            "duration": round(duration, 2),
        }

    except Exception as e:
        logger.error(f"Voice emotion analysis failed: {e}")
        return _default_voice_features(error=str(e))


def _calculate_voice_confidence(
    pitch_mean: float,
    pitch_std: float,
    energy_mean: float,
    energy_std: float,
    pause_ratio: float,
    hesitation_detected: bool,
    zcr_mean: float,
) -> float:
    """Calculate a confidence score from voice features.
    
    Returns:
        Confidence score from 0 to 100.
    """
    score = 50.0  # Base score

    # Moderate pitch variation is good (not monotone, not erratic)
    if 20 < pitch_std < 100:
        score += 10
    elif pitch_std > 150:
        score -= 5

    # Higher energy generally indicates confidence
    if energy_mean > 0.02:
        score += 10
    elif energy_mean < 0.005:
        score -= 10

    # Too many pauses indicate uncertainty
    if pause_ratio < 0.3:
        score += 10
    elif pause_ratio > 0.6:
        score -= 15

    # Hesitations reduce confidence
    if hesitation_detected:
        score -= 15

    # Very high zcr might indicate shaky voice
    if zcr_mean > 0.15:
        score -= 5

    return max(0.0, min(100.0, score))


def _infer_emotion(
    pitch_mean: float,
    pitch_std: float,
    energy_mean: float,
    pause_ratio: float,
) -> str:
    """Infer emotion from voice features."""
    if energy_mean > 0.03 and pitch_std > 50:
        if pitch_mean > 200:
            return "excited"
        return "confident"
    elif energy_mean < 0.01 and pause_ratio > 0.5:
        return "nervous"
    elif pitch_std < 20 and energy_mean < 0.015:
        return "calm"
    elif energy_mean > 0.02:
        return "neutral"
    else:
        return "uncertain"


def _default_voice_features(error: str = "") -> Dict[str, Any]:
    """Return default voice features when analysis fails."""
    return {
        "pitch_mean": 0.0,
        "pitch_std": 0.0,
        "energy_mean": 0.0,
        "energy_std": 0.0,
        "spectral_centroid": 0.0,
        "zcr_mean": 0.0,
        "speaking_speed": 120.0,
        "pause_ratio": 0.0,
        "hesitation_detected": False,
        "short_pauses": 0,
        "emotion_label": "neutral",
        "confidence_score": 50.0,
        "duration": 0.0,
        "error": error,
    }
