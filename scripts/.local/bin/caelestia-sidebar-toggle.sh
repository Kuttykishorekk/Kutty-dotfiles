#!/bin/bash

# Script to toggle the left sidebar by changing the persistent setting
CONFIG_FILE="$HOME/.config/caelestia/shell.json"
STATE_FILE="/tmp/caelestia-bar-state"

# Check current state
if [ -f "$STATE_FILE" ] && [ "$(cat $STATE_FILE)" = "hidden" ]; then
    # Currently hidden, show it
    echo "visible" > "$STATE_FILE"
    
    # Change config to persistent (always visible)
    sed 's/"persistent": false/"persistent": true/' "$CONFIG_FILE" > /tmp/caelestia-temp.json
    mv /tmp/caelestia-temp.json "$CONFIG_FILE"
    
    # Restart Caelestia to apply changes
    caelestia shell -k
    sleep 1
    caelestia shell -d &
    
    notify-send "Caelestia" "Left sidebar shown" -t 1000
else
    # Currently visible, hide it
    echo "hidden" > "$STATE_FILE"
    
    # Change config to non-persistent (can be hidden)
    sed 's/"persistent": true/"persistent": false/' "$CONFIG_FILE" > /tmp/caelestia-temp.json
    mv /tmp/caelestia-temp.json "$CONFIG_FILE"
    
    # Restart Caelestia to apply changes
    caelestia shell -k
    sleep 1
    caelestia shell -d &
    
    notify-send "Caelestia" "Left sidebar hidden" -t 1000
fi