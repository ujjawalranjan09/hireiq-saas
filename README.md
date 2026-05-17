<div align="center">

# 🎯 AI Multimodal Interview Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*A production-grade AI system that conducts adaptive technical interviews with real-time emotion detection, voice analysis, and automated PDF report generation.*

</div>

---

## 🎯 What This Project Does

This is a **full-stack multimodal AI interview platform** that replaces a human interviewer. A candidate uploads their resume, the system parses it, generates adaptive questions, listens to voice answers, analyzes facial emotion in real-time, and produces a detailed PDF performance report at the end.

> 📊 **Multimodal Confidence Score** = 50% Facial Emotion + 30% Voice Tone + 20% Fluency

---

## ✨ Features

- **📄 Resume Parsing** — Extracts skills, projects, and candidate info from PDF resumes
- **🧠 Adaptive Difficulty** — Questions auto-adjust Easy → Medium → Hard → Expert based on performance
- **🎤 Voice Input** — OpenAI Whisper speech-to-text for answering questions by voice
- **📹 Facial Emotion Detection** — Real-time analysis via DeepFace (7 emotion classes)
- **🎧 Voice Emotion Analysis** — Pitch, speed, and hesitation detection via librosa
- **📊 7 Visualization Charts** — Bar, line, area, radar, pie, step, and grouped bar charts (Plotly)
- **📄 PDF Report Generation** — Comprehensive multi-page report with FPDF2
- **🔄 Interview Replay** — Review past interviews with full emotion timeline
- **💾 MongoDB Storage** — Persistent storage of all interview sessions, questions, emotions

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Database | MongoDB (pymongo) |
| NLP | sentence-transformers, spaCy |
| Speech Recognition | OpenAI Whisper |
| Text-to-Speech | gTTS / pyttsx3 |
| Video / Emotion | OpenCV, DeepFace |
| Audio Analysis | librosa |
| Charts | Plotly |
| PDF Generation | FPDF2 |
| Containerization | Docker + Docker Compose |

---

## 📊 Scoring System

### Answer Score (0–100)
```
Score = 0.4 × Semantic Similarity + 0.3 × Keyword Match + 0.3 × Concept Coverage
```

### Confidence Score (0–100)
```
Confidence = 0.5 × Facial Emotion + 0.3 × Voice Tone + 0.2 × Fluency
```

### Adaptive Difficulty Logic
- Starts at **Medium** (Level 2)
- Rolling average of last 3 answers:
  - ≥85 → Harder | 60–84 → Same | 40–59 → Easier | <40 → Easy

---

## 🚀 Quick Start

### Option 1: Local Setup

```bash
# Clone the repository
git clone https://github.com/ujjawalranjan09/ai-interview-agent.git
cd ai-interview-agent

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Ensure MongoDB is running
mongod --dbpath /path/to/data

# Launch the app
streamlit run app/main.py
```

### Option 2: Docker

```bash
git clone https://github.com/ujjawalranjan09/ai-interview-agent.git
cd ai-interview-agent
docker-compose up --build
# Access at http://localhost:8501
```

---

## ⚙️ Configuration

Edit `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `WHISPER_MODEL` | `base` | Model size: tiny/base/small/medium/large |
| `TTS_ENGINE` | `gtts` | TTS engine: gtts or pyttsx3 |
| `DEFAULT_QUESTIONS_COUNT` | `10` | Number of interview questions |

---

## 🏗️ Architecture

```
ai-interview-agent/
├── app/                    # Streamlit entry & config
├── modules/
│   ├── orchestrator/       # Interview flow control
│   ├── resume/             # PDF parsing & skill extraction
│   ├── questions/          # Question generation & difficulty
│   ├── voice/              # STT, TTS, voice emotion
│   ├── video/              # Camera & facial emotion
│   ├── evaluation/         # Answer scoring & confidence
│   ├── analytics/          # Performance metrics & charts
│   └── report/             # Feedback, PDF generation, replay
├── database/               # MongoDB models & queries
├── frontend/               # Streamlit pages & components
├── tests/                  # pytest test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage report
pip install pytest-cov
python -m pytest tests/ --cov=modules --cov-report=html
```

---

## 🔄 Interview State Machine

```
IDLE → RESUME_PROCESSING → READY → INTRODUCTION → ASKING_QUESTION
→ LISTENING → PROCESSING_ANSWER → [GENERATING_FOLLOWUP → ASKING_FOLLOWUP]
→ SELECTING_NEXT_QUESTION → CLOSING → GENERATING_REPORT → COMPLETED
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ by [Ujjawal Ranjan](https://github.com/ujjawalranjan09) | RTU, Jaipur**

*Redefining technical interviews with multimodal AI.*

</div>
