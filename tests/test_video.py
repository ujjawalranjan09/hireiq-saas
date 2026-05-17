"""Tests for the video module."""

import unittest
import numpy as np


class TestEmotionDetector(unittest.TestCase):
    """Test emotion detection."""

    def test_get_emotion_summary_empty(self):
        """Test summary with no data."""
        from modules.video.emotion_detector import get_emotion_summary
        summary = get_emotion_summary([])
        self.assertEqual(summary["dominant_emotion"], "neutral")
        self.assertEqual(summary["face_detection_rate"], 0.0)

    def test_get_emotion_summary(self):
        """Test summary with data."""
        from modules.video.emotion_detector import get_emotion_summary
        results = [
            {"dominant_emotion": "happy", "confidence_score": 80, "face_detected": True},
            {"dominant_emotion": "happy", "confidence_score": 75, "face_detected": True},
            {"dominant_emotion": "neutral", "confidence_score": 60, "face_detected": True},
        ]
        summary = get_emotion_summary(results)
        self.assertEqual(summary["dominant_emotion"], "happy")
        self.assertEqual(summary["total_frames"], 3)
        self.assertAlmostEqual(summary["face_detection_rate"], 1.0)

    def test_emotion_to_confidence(self):
        """Test emotion to confidence conversion."""
        from modules.video.emotion_detector import _emotion_to_confidence
        # Happy should give higher confidence than angry
        happy_score = _emotion_to_confidence("happy", {"happy": 0.8})
        angry_score = _emotion_to_confidence("angry", {"angry": 0.8})
        self.assertGreater(happy_score, angry_score)


class TestEmotionTracker(unittest.TestCase):
    """Test emotion tracking."""

    def test_tracker_initialization(self):
        """Test tracker creation."""
        from modules.video.emotion_tracker import EmotionTracker
        tracker = EmotionTracker(window_size=5)
        summary = tracker.get_summary()
        self.assertEqual(summary["dominant_emotion"], "neutral")

    def test_tracker_add_emotion(self):
        """Test adding emotions."""
        from modules.video.emotion_tracker import EmotionTracker
        tracker = EmotionTracker(window_size=3)
        result = tracker.add_emotion({
            "dominant_emotion": "happy",
            "confidence_score": 80,
            "face_detected": True,
        })
        self.assertIn("smoothed_emotion", result)
        self.assertEqual(len(tracker.timeline), 1)

    def test_tracker_smoothing(self):
        """Test emotion smoothing."""
        from modules.video.emotion_tracker import EmotionTracker
        tracker = EmotionTracker(window_size=3)
        # Add mix of emotions
        for emotion in ["happy", "happy", "sad"]:
            tracker.add_emotion({
                "dominant_emotion": emotion,
                "confidence_score": 70,
                "face_detected": True,
            })
        summary = tracker.get_summary()
        # Majority should win
        self.assertEqual(summary["dominant_emotion"], "happy")

    def test_tracker_reset(self):
        """Test tracker reset."""
        from modules.video.emotion_tracker import EmotionTracker
        tracker = EmotionTracker()
        tracker.add_emotion({"dominant_emotion": "happy", "confidence_score": 80, "face_detected": True})
        tracker.reset()
        self.assertEqual(len(tracker.timeline), 0)


if __name__ == "__main__":
    unittest.main()
