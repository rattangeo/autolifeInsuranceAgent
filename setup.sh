#!/bin/bash
# Quick setup script for Insurance Claims Agent

echo "🏥 Insurance Claims Processing Agent - Setup"
echo "==========================================="
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo
echo "✅ Setup complete!"
echo
echo "To run the agent:"
echo "  source venv/bin/activate"
echo "  python main.py --sample 1    # Test with sample claim"
echo "  python main.py --interactive # Interactive mode"
echo "  python main.py --help        # See all options"
echo
