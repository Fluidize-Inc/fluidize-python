#!/bin/bash
# Fluidize-Python Jupyter Notebook Launcher

set -e  # Exit on error

echo "🚀 Starting Fluidize-Python Jupyter Notebook"
echo "============================================="

# Change to project root directory (parent of utils)
cd "$(dirname "$0")/.."

# Ensure uv environment is set up
echo "📦 Setting up uv environment..."
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first: https://github.com/astral-sh/uv"
    exit 1
fi

# Sync dependencies and install package in development mode
uv sync
echo "📦 Installing package in development mode..."
uv run pip install -e .

# Check if jupyter is installed in the uv environment
echo "📚 Ensuring Jupyter is available..."
if ! uv run jupyter --version &> /dev/null; then
    echo "📚 Adding Jupyter to uv environment..."
    uv add --dev jupyter
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
uv run jupyter notebook --notebook-dir=. utils/fluidize_demo.ipynb
