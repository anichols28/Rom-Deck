#!/bin/bash

# ROM Downloader - Linux launcher
# This script runs romdownloader.py on Linux systems

# Get the directory where this script is located
# Use BASH_SOURCE if available, fall back to $0 (needed when launched from Steam)
SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"

# Resolve symlinks to get the real script path
if command -v readlink &> /dev/null; then
    SCRIPT_SOURCE="$(readlink -f "$SCRIPT_SOURCE" 2>/dev/null || echo "$SCRIPT_SOURCE")"
fi

SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" 2>/dev/null && pwd)"

# Fallback: if SCRIPT_DIR is empty or invalid, try the current working directory
if [ -z "$SCRIPT_DIR" ] || [ ! -d "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$(pwd)"
fi

# Verify the Python script actually exists in SCRIPT_DIR
if [ ! -f "$SCRIPT_DIR/romdownloader.py" ]; then
    echo "Error: Cannot find romdownloader.py in $SCRIPT_DIR"
    echo "Make sure romdownloader.sh and romdownloader.py are in the same folder."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Auto-install Steam controller config if on Steam Deck and not already installed
if [ -d "$HOME/.local/share/Steam" ] || [ -d "$HOME/.steam/steam" ]; then
    # Find Steam path
    STEAM_PATH="$HOME/.local/share/Steam"
    [ ! -d "$STEAM_PATH" ] && STEAM_PATH="$HOME/.steam/steam"
    
    # Check if controller config exists
    CONTROLLER_DIR="$STEAM_PATH/controller_base/templates"
    DEST_FILE="$CONTROLLER_DIR/rom_downloader_default.vdf"
    CONFIG_FILE="$SCRIPT_DIR/controller_config.vdf"
    
    if [ -f "$CONFIG_FILE" ] && [ ! -f "$DEST_FILE" ]; then
        echo "Installing Steam controller configuration..."
        mkdir -p "$CONTROLLER_DIR"
        cp "$CONFIG_FILE" "$DEST_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓ Controller config installed! Select 'ROM Downloader Controls' template in Steam."
        fi
    fi
fi

# Change to script directory so relative paths work
cd "$SCRIPT_DIR"

# Run the Python script
python3 "$SCRIPT_DIR/romdownloader.py"
