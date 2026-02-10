#!/bin/bash

# Stats Solver Installation Script
# This script helps install Stats Solver and its dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended. Please run without sudo."
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    print_error "Python 3.9 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_info "Python version $PYTHON_VERSION detected."

# Check if pip is available
print_info "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip first."
    exit 1
fi

# Ask for LLM provider
echo ""
print_info "Stats Solver requires a local LLM. Which provider would you like to use?"
echo "1) Ollama (recommended)"
echo "2) LM Studio"
echo "3) Skip LLM setup (configure later)"
read -p "Enter choice [1-3]: " llm_choice

# Install Python dependencies
print_info "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -e .

# Copy environment file
if [ ! -f .env ]; then
    print_info "Creating .env file..."
    cp .env.example .env

    # Configure LLM based on user choice
    case $llm_choice in
        1)
            print_info "Configuring for Ollama..."
            sed -i 's/LLM_PROVIDER=.*/LLM_PROVIDER=ollama/' .env
            sed -i 's/LLM_PORT=.*/LLM_PORT=11434/' .env

            # Check if Ollama is installed
            if command -v ollama &> /dev/null; then
                print_info "Ollama detected. Available models:"
                ollama list 2>/dev/null || echo "  (No models found)"

                read -p "Enter model name [llama3]: " model_name
                model_name=${model_name:-llama3}
                sed -i "s/LLM_MODEL=.*/LLM_MODEL=$model_name/" .env

                print_info "Testing Ollama connection..."
                ollama run $model_name "Hello" 2>/dev/null && print_info "Ollama connection successful!" || print_warning "Could not connect to Ollama. Please ensure it's running."
            else
                print_warning "Ollama not detected. Please install it from https://ollama.ai"
            fi
            ;;
        2)
            print_info "Configuring for LM Studio..."
            sed -i 's/LLM_PROVIDER=.*/LLM_PROVIDER=lm_studio/' .env
            sed -i 's/LLM_PORT=.*/LLM_PORT=1234/' .env

            read -p "Enter LM Studio model name: " model_name
            sed -i "s/LLM_MODEL=.*/LLM_MODEL=$model_name/" .env

            print_warning "Please ensure LM Studio is running with the server enabled."
            ;;
        3)
            print_info "Skipping LLM setup. You can configure it later by editing .env"
            ;;
    esac
else
    print_warning ".env file already exists. Skipping configuration."
fi

# Create output directory
print_info "Creating output directory..."
mkdir -p output

# Initialize skill index
print_info "Initializing skill index..."
stats-solver init || print_warning "Could not initialize skills. Please run 'stats-solver init' manually."

# Check installation
print_info "Verifying installation..."
if command -v stats-solver &> /dev/null; then
    print_info "Stats Solver installed successfully!"
    echo ""
    echo "Quick Start:"
    echo "  stats-solver check    # Check system status"
    echo "  stats-solver solve    # Get recommendations"
    echo "  stats-solver --help   # Show all commands"
    echo ""
    echo "Documentation: https://stats-solver.readthedocs.io"
else
    print_error "Installation verification failed. Please check the output above."
    exit 1
fi

print_info "Installation complete!"