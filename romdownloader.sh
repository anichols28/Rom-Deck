#!/bin/bash

# ROM Downloader - Linux launcher
# This script runs romdownloader.py on Linux systems

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

# Run the Python script
python3 "$SCRIPT_DIR/romdownloader.py"
