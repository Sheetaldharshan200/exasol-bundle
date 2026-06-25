#!/bin/bash
# Universal installer for macOS and Linux (curl -fsSL url | bash)
set -e

echo "=== Exasol Universal Installer ==="

# Check for uv (Preferred for speed and isolation)
if command -v uv &> /dev/null; then
    echo "Detected 'uv'. Installing via uv tool..."
    uv tool install exa-bundle
    exa-bundle init
    exit 0
fi

# Check for pipx (Preferred standard isolation)
if command -v pipx &> /dev/null; then
    echo "Detected 'pipx'. Installing via pipx..."
    pipx install exa-bundle
    exa-bundle init
    exit 0
fi

# Fallback to standard pip
if command -v python3 &> /dev/null; then
    echo "Detected python3. Installing via pip..."
    python3 -m pip install --user exa-bundle
    
    # Ensure local bin is in PATH for the current session
    export PATH="$HOME/.local/bin:$PATH"
    
    exa-bundle init
    exit 0
fi

echo "Error: Neither 'uv', 'pipx', nor 'python3' was found on your system."
echo "Please install Python 3.9+ to continue."
exit 1