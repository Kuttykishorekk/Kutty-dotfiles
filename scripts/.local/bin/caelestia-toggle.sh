#!/bin/bash
if pgrep -f "qs -c caelestia" > /dev/null; then
    pkill -f "qs -c caelestia"
    echo "Caelestia stopped"
else
    sleep 2 && caelestia shell -d &
    echo "Caelestia started"
fi
