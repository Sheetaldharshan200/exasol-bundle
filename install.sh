#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== Exasol Universal Installer ===${NC}"

# Function to auto-install Python based on the OS
bootstrap_python() {
    echo -e "${YELLOW}[WARN] Python 3 is missing. Attempting to install it automatically...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install python
        else
            echo -e "${RED}[ERROR] Homebrew not found. Please install Python manually.${NC}"
            exit 1
        fi
    elif command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}[INFO] Python 3 is missing. The following command will be run:${NC}"
        echo "  sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
        read -r -p "Proceed? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[CANCELLED] Please install Python 3 manually, then re-run this script.${NC}"
            exit 1
        fi
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf &> /dev/null; then
        echo -e "${YELLOW}[INFO] Python 3 is missing. The following command will be run:${NC}"
        echo "  sudo dnf install -y python3 python3-pip"
        read -r -p "Proceed? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[CANCELLED] Please install Python 3 manually, then re-run this script.${NC}"
            exit 1
        fi
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        echo -e "${YELLOW}[INFO] Python 3 is missing. The following command will be run:${NC}"
        echo "  sudo pacman -S --noconfirm python python-pip"
        read -r -p "Proceed? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[CANCELLED] Please install Python 3 manually, then re-run this script.${NC}"
            exit 1
        fi
        sudo pacman -S --noconfirm python python-pip
    elif command -v zypper &> /dev/null; then
        echo -e "${YELLOW}[INFO] Python 3 is missing. The following command will be run:${NC}"
        echo "  sudo zypper install -y python3 python3-pip"
        read -r -p "Proceed? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo -e "${RED}[CANCELLED] Please install Python 3 manually, then re-run this script.${NC}"
            exit 1
        fi
        sudo zypper install -y python3 python3-pip
    else
        echo -e "${RED}[ERROR] Could not detect a supported package manager. Please install Python 3 manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}[SUCCESS] Python 3 installed successfully.${NC}\n"
}

# 1. Check for Python, install if missing
if ! command -v python3 &> /dev/null; then
    bootstrap_python
fi

INSTALL_METHOD=""

# 2. Determine best installation method
if command -v uv &> /dev/null; then
    INSTALL_METHOD="uv tool install"
    echo -e "${GREEN}[INFO] Detected 'uv'. Using optimized tool installer.${NC}"
elif command -v pipx &> /dev/null; then
    INSTALL_METHOD="pipx install"
    echo -e "${GREEN}[INFO] Detected 'pipx'. Using isolated environment installer.${NC}"
else
    INSTALL_METHOD="python3 -m pip install --user"
    echo -e "${YELLOW}[WARN] 'uv' or 'pipx' not found. Falling back to standard pip install.${NC}"
fi

# 3. Execute Installation
echo "Installing Exasol Bundle..."
$INSTALL_METHOD exasol-bundle

# 4. Path Management
if [[ "$INSTALL_METHOD" == *"pip install"* ]]; then
    LOCAL_BIN="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        echo -e "\n${YELLOW}[ACTION REQUIRED] The CLI was installed to ${LOCAL_BIN}, which is not in your PATH.${NC}"
        echo "To use the CLI in future sessions, add this to your ~/.bashrc or ~/.zshrc:"
        echo -e "${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
    export PATH="$LOCAL_BIN:$PATH"
fi

# 5. Initialization
echo -e "\n${GREEN}[SUCCESS] Installation complete! Running initialization...${NC}"
exa-bundle init