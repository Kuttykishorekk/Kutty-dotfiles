#!/bin/bash
# Waybar toggle script for HyDE
# Toggles waybar and ensures Caelestia/Quickshell is stopped when Waybar is active.

if pgrep -x waybar > /dev/null; then
    pkill -x waybar
    notify-send "Desktop Shell" "Waybar Stopped" -i info -t 1500
else
    # Ensure Caelestia is stopped to prevent overlapping bars
    pkill -f "qs -c caelestia" 2>/dev/null
    pkill -x quickshell 2>/dev/null
    
    # Start Waybar
    waybar &
    notify-send "Desktop Shell" "Waybar Started" -i info -t 1500
fi
