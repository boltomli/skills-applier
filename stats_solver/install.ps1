# Stats Solver Installation Script for Windows
# This script helps install Stats Solver and its dependencies

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info {
    Write-ColorOutput Green "[INFO] $args"
}

function Write-Warning {
    Write-ColorOutput Yellow "[WARN] $args"
}

function Write-Error {
    Write-ColorOutput Red "[ERROR] $args"
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Warning "Running as administrator is not recommended. Please run without administrator privileges."
    exit 1
}

# Check Python version
Write-Info "Checking Python version..."
try {
    $pythonVersion = python --version 2>&1
    Write-Info "Python version: $pythonVersion"

    $versionParts = $pythonVersion -split ' '
    $versionNumber = $versionParts[1]
    $major, $minor = $versionNumber -split '\.'

    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 9)) {
        Write-Error "Python 3.9 or higher is required. Current version: $versionNumber"
        exit 1
    }
} catch {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# Check if pip is available
Write-Info "Checking pip..."
try {
    pip --version | Out-Null
} catch {
    Write-Error "pip is not installed. Please install pip first."
    exit 1
}

# Ask for LLM provider
Write-Info "Stats Solver requires a local LLM. Which provider would you like to use?"
Write-Host "1) Ollama (recommended)"
Write-Host "2) LM Studio"
Write-Host "3) Skip LLM setup (configure later)"
$llmChoice = Read-Host "Enter choice [1-3]"

# Install Python dependencies
Write-Info "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -e .

# Copy environment file
if (-not (Test-Path .env)) {
    Write-Info "Creating .env file..."
    Copy-Item .env.example .env

    # Configure LLM based on user choice
    $envContent = Get-Content .env

    switch ($llmChoice) {
        "1" {
            Write-Info "Configuring for Ollama..."
            $envContent = $envContent -replace 'LLM_PROVIDER=.*', 'LLM_PROVIDER=ollama'
            $envContent = $envContent -replace 'LLM_PORT=.*', 'LLM_PORT=11434'

            # Check if Ollama is installed
            try {
                ollama list | Out-Null
                Write-Info "Ollama detected."

                $modelName = Read-Host "Enter model name [llama3]"
                if ([string]::IsNullOrWhiteSpace($modelName)) {
                    $modelName = "llama3"
                }
                $envContent = $envContent -replace 'LLM_MODEL=.*', "LLM_MODEL=$modelName"

                Write-Info "Testing Ollama connection..."
                try {
                    ollama run $modelName "Hello" 2>&1 | Out-Null
                    Write-Info "Ollama connection successful!"
                } catch {
                    Write-Warning "Could not connect to Ollama. Please ensure it's running."
                }
            } catch {
                Write-Warning "Ollama not detected. Please install it from https://ollama.ai"
            }
        }
        "2" {
            Write-Info "Configuring for LM Studio..."
            $envContent = $envContent -replace 'LLM_PROVIDER=.*', 'LLM_PROVIDER=lm_studio'
            $envContent = $envContent -replace 'LLM_PORT=.*', 'LLM_PORT=1234'

            $modelName = Read-Host "Enter LM Studio model name"
            $envContent = $envContent -replace 'LLM_MODEL=.*', "LLM_MODEL=$modelName"

            Write-Warning "Please ensure LM Studio is running with the server enabled."
        }
        "3" {
            Write-Info "Skipping LLM setup. You can configure it later by editing .env"
        }
    }

    $envContent | Set-Content .env
} else {
    Write-Warning ".env file already exists. Skipping configuration."
}

# Create output directory
Write-Info "Creating output directory..."
if (-not (Test-Path output)) {
    New-Item -ItemType Directory -Path output | Out-Null
}

# Initialize skill index
Write-Info "Initializing skill index..."
try {
    stats-solver init | Out-Null
} catch {
    Write-Warning "Could not initialize skills. Please run 'stats-solver init' manually."
}

# Check installation
Write-Info "Verifying installation..."
try {
    stats-solver --version | Out-Null
    Write-Info "Stats Solver installed successfully!"
    Write-Host ""
    Write-Host "Quick Start:"
    Write-Host "  stats-solver check    # Check system status"
    Write-Host "  stats-solver solve    # Get recommendations"
    Write-Host "  stats-solver --help   # Show all commands"
    Write-Host ""
    Write-Host "Documentation: https://stats-solver.readthedocs.io"
} catch {
    Write-Error "Installation verification failed. Please check the output above."
    exit 1
}

Write-Info "Installation complete!"
