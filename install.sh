#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/.local/share/invisible-terminal/venv"

echo "=== Invisible Terminal Installer ==="

# Create virtual environment with system packages (for PyGObject)
echo "[1/4] Creating virtual environment..."
mkdir -p "$(dirname "$VENV_DIR")"
python3 -m venv --system-site-packages "$VENV_DIR"

# Install dependencies
echo "[2/4] Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -e "$SCRIPT_DIR"

# Ensure ~/.local/bin exists and is in PATH
echo "[3/4] Setting up 'exitt' command..."
mkdir -p "$HOME/.local/bin"
ln -sf "$VENV_DIR/bin/exitt" "$HOME/.local/bin/exitt"

# Create default config if not exists
echo "[4/4] Creating default config..."
if [ ! -f "$HOME/.config/invisible-terminal/config.toml" ]; then
    mkdir -p "$HOME/.config/invisible-terminal"
    cp "$SCRIPT_DIR/config.toml.example" "$HOME/.config/invisible-terminal/config.toml"
    echo "  Config created at ~/.config/invisible-terminal/config.toml"
else
    echo "  Config already exists, skipping"
fi

echo ""
echo "=== Installation complete ==="
echo "Run 'exitt' to launch Invisible Terminal"
echo ""
echo "Shortcuts:"
echo "  Ctrl+S        — Toggle stealth/normal mode"
echo "  Ctrl+Up/Down  — Adjust text darkness"
echo "  Ctrl+Shift+H  — Panic hide/show (global hotkey)"
echo "  Ctrl+L        — Clear chat"
echo "  Ctrl+Q        — Quit"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "[note] ~/.local/bin is not in your PATH. Add this to your ~/.bashrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi
