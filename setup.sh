#!/bin/bash
# AI Interview Agent - One-click setup script

set -e

echo "🎯 AI Multimodal Interview Agent - Setup"
echo "========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
python -m spacy download en_core_web_sm || echo "⚠️  spaCy model download failed. You can install it later."

# Create directories
echo "📁 Creating output directories..."
mkdir -p outputs/reports outputs/recordings outputs/graphs outputs/temp
mkdir -p assets/sample_resumes assets/reference_answers

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from example..."
    cp .env.example .env
    echo "📝 Please edit .env to configure your settings."
fi

# Check MongoDB
if command -v mongod &> /dev/null; then
    echo "✅ MongoDB found locally"
else
    echo "⚠️  MongoDB not found locally. Use Docker Compose or install MongoDB."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  streamlit run app/main.py"
echo ""
echo "Or with Docker:"
echo "  docker-compose up --build"
echo ""
