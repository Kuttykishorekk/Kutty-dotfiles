#!/bin/bash

# Caelestia Update Script
# Updates Caelestia Shell if installed via AUR

echo "🔄 Updating Caelestia Shell..."
echo ""

# Check if installed via AUR
if pacman -Q caelestia-shell &>/dev/null; then
    echo "📦 Caelestia is installed via AUR package"
    echo "🔄 Updating via yay..."
    echo ""
    yay -Syu caelestia-shell
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Caelestia updated successfully!"
        echo ""
        echo "🔄 Restarting Caelestia shell..."
        pkill caelestia
        sleep 1
        caelestia shell -d &
        echo "✅ Caelestia restarted!"
    else
        echo ""
        echo "❌ Update failed. Please check the output above."
    fi
elif [ -d "$XDG_CONFIG_HOME/quickshell/caelestia/.git" ] || [ -d "$HOME/.config/quickshell/caelestia/.git" ]; then
    echo "📦 Caelestia is installed manually (git repository)"
    echo "🔄 Updating via git pull..."
    echo ""
    
    CAELESTIA_DIR="$XDG_CONFIG_HOME/quickshell/caelestia"
    if [ ! -d "$CAELESTIA_DIR" ]; then
        CAELESTIA_DIR="$HOME/.config/quickshell/caelestia"
    fi
    
    cd "$CAELESTIA_DIR" || exit 1
    git pull
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Caelestia updated successfully!"
        echo ""
        echo "🔄 Restarting Caelestia shell..."
        pkill caelestia
        sleep 1
        caelestia shell -d &
        echo "✅ Caelestia restarted!"
    else
        echo ""
        echo "❌ Update failed. Please check the output above."
    fi
else
    echo "❌ Could not determine Caelestia installation method."
    echo ""
    echo "If installed via AUR, run: yay -Syu caelestia-shell"
    echo "If installed manually, run: cd ~/.config/quickshell/caelestia && git pull"
fi














