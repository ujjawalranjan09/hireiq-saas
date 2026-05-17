"""
Configuration module for AI Multimodal Interview Agent.
Loads environment variables and provides centralized configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
ASSETS_DIR = BASE_DIR / "assets"
REPORTS_DIR = OUTPUTS_DIR / "reports"
RECORDINGS_DIR = OUTPUTS_DIR / "recordings"
GRAPHS_DIR = OUTPUTS_DIR / "graphs"

# Ensure output directories exist
for d in [OUTPUTS_DIR, REPORTS_DIR, RECORDINGS_DIR, GRAPHS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "interview_agent")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Whisper Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# TTS Configuration
TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")  # gtts or pyttsx3
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en")

# Video Configuration
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "480"))

# NLP Configuration
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# Interview Configuration
DEFAULT_QUESTIONS_COUNT = int(os.getenv("DEFAULT_QUESTIONS_COUNT", "10"))
MAX_FOLLOW_UPS = int(os.getenv("MAX_FOLLOW_UPS", "2"))
FOLLOW_UP_PROBABILITY = float(os.getenv("FOLLOW_UP_PROBABILITY", "0.3"))

# Scoring weights
CONFIDENCE_WEIGHTS = {
    "facial": 0.5,
    "voice_tone": 0.3,
    "fluency": 0.2,
}

ANSWER_WEIGHTS = {
    "semantic": 0.4,
    "keywords": 0.3,
    "concepts": 0.3,
}

# Question type distribution
QUESTION_WEIGHTS = {
    "resume": 0.4,
    "technical": 0.4,
    "behavioral": 0.2,
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Streamlit
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
