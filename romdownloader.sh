#!/bin/bash

# ROM Downloader - Linux launcher
# Prefers the pre-built binary (no dependencies needed).
# Falls back to Python if the binary isn't available.

BINARY_URL="https://github.com/anichols28/Rom-Deck/releases/download/latest/romdownloader"

# Get the directory where this script is located
SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
if command -v readlink &> /dev/null; then
    SCRIPT_SOURCE="$(readlink -f "$SCRIPT_SOURCE" 2>/dev/null || echo "$SCRIPT_SOURCE")"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" 2>/dev/null && pwd)"
if [ -z "$SCRIPT_DIR" ] || [ ! -d "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$(pwd)"
fi

# Change to script directory so relative paths work
cd "$SCRIPT_DIR"

# Auto-install Steam controller config if on Steam Deck
if [ -d "$HOME/.local/share/Steam" ] || [ -d "$HOME/.steam/steam" ]; then
    STEAM_PATH="$HOME/.local/share/Steam"
    [ ! -d "$STEAM_PATH" ] && STEAM_PATH="$HOME/.steam/steam"
    CONTROLLER_DIR="$STEAM_PATH/controller_base/templates"
    DEST_FILE="$CONTROLLER_DIR/rom_downloader_default.vdf"
    CONFIG_FILE="$SCRIPT_DIR/controller_config.vdf"
    if [ -f "$CONFIG_FILE" ] && [ ! -f "$DEST_FILE" ]; then
        echo "Installing Steam controller configuration..."
        mkdir -p "$CONTROLLER_DIR"
        cp "$CONFIG_FILE" "$DEST_FILE" 2>/dev/null
        [ $? -eq 0 ] && echo "Controller config installed!"
    fi
fi

# Auto-update from GitHub
REPO_URL="https://github.com/anichols28/Rom-Deck.git"
if command -v git &> /dev/null; then
    if [ ! -d "$SCRIPT_DIR/.git" ]; then
        echo "Setting up auto-updates..."
        TEMP_CLONE=$(mktemp -d)
        if git clone -q "$REPO_URL" "$TEMP_CLONE" 2>/dev/null; then
            mv "$TEMP_CLONE/.git" "$SCRIPT_DIR/.git"
            rm -rf "$TEMP_CLONE"
            git -C "$SCRIPT_DIR" checkout -- . 2>/dev/null
            echo "Auto-updates enabled."
        else
            rm -rf "$TEMP_CLONE"
            echo "Could not set up auto-updates (no internet?)"
        fi
    else
        echo "Checking for updates..."
        git pull -q origin main 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "Up to date."
        else
            echo "Update check failed (no internet?) - launching anyway."
        fi
    fi
fi

# --- Launch the app ---

# Option 1: Pre-built binary (no Python/pip/dependencies needed)
BINARY="$SCRIPT_DIR/romdownloader"
if [ -f "$BINARY" ] && [ -x "$BINARY" ]; then
    echo "Launching ROM Downloader..."
    exec "$BINARY"
fi

# Binary not found - try to download it
echo "Downloading ROM Downloader binary..."
if command -v curl &> /dev/null; then
    curl -sL -o "$BINARY" "$BINARY_URL" 2>/dev/null
elif command -v wget &> /dev/null; then
    wget -q -O "$BINARY" "$BINARY_URL" 2>/dev/null
fi

if [ -f "$BINARY" ]; then
    chmod +x "$BINARY"
    echo "Download complete. Launching..."
    exec "$BINARY"
fi

# Option 2: Fall back to Python (for development or if download failed)
echo "Binary not available, falling back to Python..."
if command -v python3 &> /dev/null && [ -f "$SCRIPT_DIR/romdownloader.py" ]; then
    python3 "$SCRIPT_DIR/romdownloader.py"
else
    echo "Error: Could not find romdownloader binary or Python 3."
    echo "Download the binary from: $BINARY_URL"
    read -p "Press Enter to exit..."
    exit 1
fi
