#!/usr/bin/env bash

# Caelestia Battery Notification Script
# Sends notifications when battery exceeds 80% during charging
# Notifies at 85%, 90%, 95%, and 100% (full)

scrDir=$(dirname "$(realpath "$0")")
lockFile="$XDG_RUNTIME_DIR/caelestia-battery-notify.lock"
state_file="$XDG_RUNTIME_DIR/caelestia-battery-notify.state"

# Improved lock mechanism using flock (more reliable)
exec 200>"$lockFile"
if ! flock -n 200; then
    # Check if the process is actually running
    if pgrep -f "caelestia-battery-notify.sh" > /dev/null; then
        echo "Another instance is already running (PID: $(pgrep -f 'caelestia-battery-notify.sh' | head -1))"
        exit 1
    else
        # Stale lock file, remove it
        rm -f "$lockFile"
        exec 200>"$lockFile"
        flock -n 200 || exit 1
    fi
fi

# Cleanup on exit
trap 'flock -u 200; rm -f "$lockFile"' EXIT

# Get battery info
get_battery_info() {
    local total_percentage=0
    local battery_count=0
    local battery_status=""
    
    for battery in /sys/class/power_supply/BAT*; do
        if [ -f "$battery/capacity" ] && [ -f "$battery/status" ]; then
            local status=$(<"$battery/status")
            local percentage=$(<"$battery/capacity")
            total_percentage=$((total_percentage + percentage))
            battery_count=$((battery_count + 1))
            battery_status="$status"
        fi
    done
    
    if [ $battery_count -gt 0 ]; then
        battery_percentage=$((total_percentage / battery_count))
        battery_status="$battery_status"
    else
        echo "No battery detected"
        exit 0
    fi
}

# Send notification
send_notification() {
    local level=$1
    local message=$2
    local urgency=${3:-"normal"}
    
    # Map battery levels to emoji icons (more reliable than system icons)
    local emoji=""
    case "$level" in
        85)
            emoji="🔋"
            ;;
        90)
            emoji="🔋"
            ;;
        95)
            emoji="🔋"
            ;;
        100)
            emoji="🔌"
            ;;
        *)
            emoji="🔋"
            ;;
    esac
    
    # Use notify-send with emoji in title (more reliable across icon themes)
    notify-send -a "Caelestia Power" \
        -u "$urgency" \
        -t 5000 \
        -r 9999 \
        "$emoji Battery Charged" \
        "$message"
}

# Load last notified percentage
load_state() {
    if [ -f "$state_file" ]; then
        last_notified=$(cat "$state_file" 2>/dev/null || echo "0")
    else
        last_notified=0
    fi
}

# Save last notified percentage
save_state() {
    echo "$1" > "$state_file" 2>/dev/null || true
}

# Main monitoring loop
main() {
    get_battery_info
    load_state
    
    # Only monitor if charging and above 80%
    if [[ "$battery_status" == *"Charging"* ]] || [[ "$battery_status" == *"Not"* ]]; then
        if [ "$battery_percentage" -ge 80 ]; then
            # Check for 85%, 90%, 95%, and 100%
            if [ "$battery_percentage" -ge 85 ] && [ "$last_notified" -lt 85 ]; then
                send_notification "85" "Battery is at 85%. Charging continues..." "normal"
                save_state 85
                last_notified=85
            elif [ "$battery_percentage" -ge 90 ] && [ "$last_notified" -lt 90 ]; then
                send_notification "90" "Battery is at 90%. Almost fully charged!" "normal"
                save_state 90
                last_notified=90
            elif [ "$battery_percentage" -ge 95 ] && [ "$last_notified" -lt 95 ]; then
                send_notification "95" "Battery is at 95%. Nearly full!" "normal"
                save_state 95
                last_notified=95
            elif [ "$battery_percentage" -ge 100 ] && [ "$last_notified" -lt 100 ]; then
                send_notification "100" "Battery is fully charged! You can unplug the charger." "critical"
                save_state 100
                last_notified=100
            fi
        fi
    else
        # Reset when discharging below 80%
        if [ "$battery_percentage" -lt 80 ]; then
            save_state 0
            last_notified=0
        fi
    fi
}

# Monitor battery changes using dbus
get_battery_info
prev_percentage=$battery_percentage
prev_status=$battery_status

# Get battery device path for dbus monitoring
battery_path=$(upower -e | grep battery | head -1)

if [ -n "$battery_path" ]; then
    dbus-monitor --system "type='signal',interface='org.freedesktop.DBus.Properties',path='$battery_path'" 2>/dev/null | while read -r line; do
        if echo "$line" | grep -q "PropertiesChanged"; then
            sleep 1
            get_battery_info
            
            # Only process if percentage changed
            if [ "$battery_percentage" != "$prev_percentage" ] || [ "$battery_status" != "$prev_status" ]; then
                main
                prev_percentage=$battery_percentage
                prev_status=$battery_status
            fi
        fi
    done
else
    # Fallback: poll every 5 seconds if dbus monitoring fails
    while true; do
        get_battery_info
        if [ "$battery_percentage" != "$prev_percentage" ] || [ "$battery_status" != "$prev_status" ]; then
            main
            prev_percentage=$battery_percentage
            prev_status=$battery_status
        fi
        sleep 5
    done
fi

