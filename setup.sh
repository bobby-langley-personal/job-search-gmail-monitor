#!/bin/bash

# Job Search Gmail Monitor - Setup Script
# This script helps set up the project for first-time use

set -e

echo "========================================"
echo "Job Search Gmail Monitor - Setup"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

python_version=$(python3 --version | cut -d ' ' -f 2)
echo "✅ Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create configuration files
echo "Setting up configuration files..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file - PLEASE EDIT THIS FILE with your credentials"
else
    echo "✅ .env file already exists"
fi

if [ ! -f "config/settings.yaml" ]; then
    cp config/settings.example.yaml config/settings.yaml
    echo "✅ Created config/settings.yaml - customize as needed"
else
    echo "✅ config/settings.yaml already exists"
fi
echo ""

# Create logs directory
mkdir -p logs
echo "✅ Created logs directory"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Set up Gmail API credentials:"
echo "   - Go to https://console.cloud.google.com/"
echo "   - Create a new project"
echo "   - Enable Gmail API"
echo "   - Create OAuth 2.0 credentials"
echo "   - Download credentials.json to config/ directory"
echo ""
echo "2. Edit .env file with your email/SMS credentials:"
echo "   nano .env"
echo ""
echo "3. Customize config/settings.yaml with your preferences:"
echo "   nano config/settings.yaml"
echo ""
echo "4. Run the monitor:"
echo "   python src/main.py"
echo ""
echo "For more details, see README.md"
echo ""
