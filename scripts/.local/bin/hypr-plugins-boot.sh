#!/usr/bin/env bash
# Load hyprpm plugins after Hyprland starts, then reload config so plugin
# options in hyprland.lua apply cleanly (avoids "unknown config key" on boot).
set -euo pipefail

[[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] || exit 0

# 1) Load enabled plugins into the running compositor
hyprpm reload -n

# 2) Re-parse config now that hl.plugin.* exists
sleep 0.3
hyprctl reload
