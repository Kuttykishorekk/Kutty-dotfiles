#!/bin/bash

# Window blur/transparency toggle (Super+Alt+B)
# Performance mode: blur off. Optimized mode: light blur on.
# Uses hyprctl eval because keyword does not work with Hyprland's Lua parser.

STATE_FILE="/tmp/window-blur-state"

hypr_eval() {
	hyprctl eval "$1" >/dev/null
}

if [ -f "$STATE_FILE" ] && [ "$(cat "$STATE_FILE")" = "blurred" ]; then
	echo "transparent" > "$STATE_FILE"

	hypr_eval 'hl.config({ plugin = { hyprglass = { enabled = false } } })'
	hypr_eval 'hl.config({ decoration = { blur = { enabled = false, size = 0 } } })'

	notify-send "Window Mode" "Switched to Transparent Mode" -t 1500
else
	echo "blurred" > "$STATE_FILE"

	hypr_eval 'hl.config({ plugin = { hyprglass = { enabled = false } } })'
	hypr_eval 'hl.config({
		decoration = {
			blur = {
				enabled = true,
				size = 6,
				passes = 1,
				new_optimizations = true,
				xray = false,
				ignore_opacity = true,
				noise = 0.01,
				contrast = 0.92,
				brightness = 0.9,
				popups = true,
				popups_ignorealpha = 0.2,
			},
		},
	})'

	notify-send "Window Mode" "Switched to Blurred Mode (Optimized)" -t 1500
fi
