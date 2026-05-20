#!/bin/bash

# Quick Restore Script
# Use this to quickly restore your dotfiles on a fresh Arch install
# Combines git clone + install.sh into one command

set -e

REPO_URL="https://github.com/Kuttykishorekk/Kutty-dotfiles"  # Update this!
INSTALL_DIR="$HOME/kutty-dotfiles"

echo "🚀 Kutty's Dotfiles Quick Restore"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "   Please install git first: sudo pacman -S git"
    exit 1
fi

# Clone the repo (or pull if it already exists)
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Dotfiles repo already exists. Pulling latest..."
    cd "$INSTALL_DIR"
    git pull origin main 2>/dev/null || git pull origin master
else
    echo "📥 Cloning dotfiles repository..."
    git clone "$REPO_URL" "$INSTALL_DIR" || {
        echo "❌ Error: Could not clone repository"
        echo "   Make sure REPO_URL is set correctly in this script"
        echo "   Current URL: $REPO_URL"
        exit 1
    }
    cd "$INSTALL_DIR"
fi

echo "✓ Repository ready at: $INSTALL_DIR"
echo ""

# Run the installer
echo "Running install.sh..."
chmod +x "$INSTALL_DIR/install.sh"
"$INSTALL_DIR/install.sh"
