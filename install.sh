#!/bin/bash

# Kutty's Dotfiles Installer
# This script sets up symlinks for Hyprland, Caelestia, and QuickShell configs
# using GNU Stow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIRS=(
    "hyprland"
    "caelestia"
    "quickshell"
    "qylock"
    "kitty"
    "zsh"
    "hyprpet"
    "hyde"
    "waybar"
    "rofi"
    "dunst"
    "wlogout"
    "fastfetch"
    "cava"
    "starship"
    "btop"
    "scripts"
)

echo "🔧 Kutty's Dotfiles Installer"
echo "================================"

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/.gitignore" ]; then
    echo "❌ Error: Run this script from the dotfiles directory root"
    exit 1
fi

# Check for GNU Stow
if ! command -v stow &> /dev/null; then
    echo "⚠️  GNU Stow not found. Installing..."
    if command -v pacman &> /dev/null; then
        echo "   Detected Arch Linux. Installing stow with pacman..."
        sudo pacman -S --noconfirm stow
    elif command -v apt &> /dev/null; then
        echo "   Detected Debian/Ubuntu. Installing stow with apt..."
        sudo apt update && sudo apt install -y stow
    elif command -v brew &> /dev/null; then
        echo "   Detected macOS. Installing stow with brew..."
        brew install stow
    else
        echo "❌ Could not auto-detect package manager. Please install GNU Stow manually."
        exit 1
    fi
fi

echo "✓ GNU Stow is available"
echo ""

# Create backups of existing configs
echo "📦 Backing up existing configs..."
BACKUP_DIR="$HOME/.config.backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

for config_dir in "${CONFIG_DIRS[@]}"; do
    LOCAL_CONFIG="$HOME/.config/$config_dir"
    if [ -e "$LOCAL_CONFIG" ]; then
        echo "   Backing up ~/.config/$config_dir → $BACKUP_DIR/"
        cp -rv "$LOCAL_CONFIG" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done

echo "✓ Backups created at: $BACKUP_DIR"
echo ""

# Ensure necessary directories exist
mkdir -p "$HOME/.config" "$HOME/.local/bin" "$HOME/.local/share" "$HOME/.local/state"

# Stow each config directory
echo "🔗 Creating symlinks with GNU Stow..."
cd "$SCRIPT_DIR"

for config_dir in "${CONFIG_DIRS[@]}"; do
    if [ -d "$config_dir" ]; then
        echo "   Stowing $config_dir..."
        stow -v "$config_dir" 2>&1 | sed 's/^/      /'
        echo "   ✓ $config_dir symlinked"
    else
        echo "   ⚠️  $config_dir not found, skipping..."
    fi
done

# Ensure executable permissions on all scripts
chmod +x "$HOME/.local/bin/"* 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Summary:"
echo "   - Config backups: $BACKUP_DIR"
echo "   - Symlinks created for: ${CONFIG_DIRS[*]}"
echo "   - Configs are now in ~/.config/ (symlinked to $SCRIPT_DIR)"
echo ""
echo "💡 Tips:"
echo "   - To update configs: git pull && stow -R hyprland caelestia quickshell"
echo "   - To unstow all: stow -D hyprland caelestia quickshell"
echo "   - Configs are version-controlled in $SCRIPT_DIR"
echo ""
echo "Need help? Check the README.md in the dotfiles directory."
