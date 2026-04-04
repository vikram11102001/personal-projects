#!/bin/bash
# LinkedIn Job Agent — Setup & Run Script

set -e

echo "=================================="
echo " 🤖 LinkedIn Job Agent Setup"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Install from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=================================="
echo " ⚙️  Configuration Check"
echo "=================================="

# Check if config has been edited
if grep -q "your_gmail@gmail.com" config.py; then
    echo ""
    echo "⚠️  IMPORTANT: You need to edit config.py first!"
    echo ""
    echo "   Open config.py and set:"
    echo "   1. sender_email    → Your Gmail address"
    echo "   2. gmail_app_password → Your Gmail App Password"
    echo "      (Generate at: https://myaccount.google.com/apppasswords)"
    echo "   3. recipient_email → Your friend's email"
    echo "   4. schedule_time   → When to send (e.g. '08:00')"
    echo ""
    echo "   Then run: bash run.sh"
    exit 0
fi

echo "✅ Config looks good!"
echo ""

# Create logs directory
mkdir -p logs

echo "=================================="
echo " 🚀 Starting Job Agent"
echo "=================================="
echo ""
echo "  The agent will:"
echo "  1. Scrape LinkedIn for AI/ML jobs in Germany RIGHT NOW"
echo "  2. Send an email digest immediately"
echo "  3. Then run again daily at the scheduled time"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

python3 job_agent.py
