#!/usr/bin/env bash

set -euo pipefail

command -v hyprctl >/dev/null 2>&1 || exit 1
command -v jq >/dev/null 2>&1 || exit 1

active_window_json="$(hyprctl activewindow -j)"
address="$(jq -r '.address // empty' <<<"$active_window_json")"

if [[ -z "$address" ]]; then
    exit 0
fi

is_floating="$(jq -r '.floating // false' <<<"$active_window_json")"

if [[ "$is_floating" == "true" ]]; then
    hyprctl dispatch centerwindow >/dev/null 2>&1 || true
else
    hyprctl dispatch layoutmsg togglesplit >/dev/null 2>&1 || true
fi
