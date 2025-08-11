#!/bin/bash
# Fluidize-Python Jupyter Notebook Launcher

set -e  # Exit on error

echo "🚀 Starting Fluidize-Python Jupyter Notebook"
echo "============================================="

# Change to project root directory (parent of utils)
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Running setup..."
    make install
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo "📚 Installing Jupyter..."
    pip install jupyter
fi

# Show environment info
echo "🐍 Python: $(which python)"
echo "📁 Projects directory: ~/.fluidize/projects/"
echo "📓 Notebook: utils/fluidize_demo.ipynb"
echo "📂 Current directory: $(pwd)"
echo ""

# Start Jupyter notebook from project root
echo "🌟 Starting Jupyter Notebook..."
echo "   The notebook will open in your browser automatically"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start Jupyter from the project root so imports work correctly
# The notebook will be available at utils/fluidize_demo.ipynb
jupyter notebook --notebook-dir=. utils/fluidize_demo.ipynb
