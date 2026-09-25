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
    hyprctl dispatch settiled "address:${address}" >/dev/null 2>&1 || true
    exit 0
fi

monitor_id="$(jq -r '.monitorID // empty' <<<"$active_window_json")"
monitors_json="$(hyprctl monitors -j)"

monitor_json="$(jq --argjson id "${monitor_id:-0}" '
    map(select(.id == $id))[0] // map(select(.focused == true))[0]
' <<<"$monitors_json")"

read -r mx my mw mh <<<"$(jq -r '
    . as $m
    | ($m.scale // 1) as $scale
    | ($m.reserved // [0,0,0,0]) as $r
    | ($m.x // 0) as $x
    | ($m.y // 0) as $y
    | (($m.width // 0) / $scale | floor) as $logical_w
    | (($m.height // 0) / $scale | floor) as $logical_h
    | ($r[0] // 0) as $top
    | ($r[1] // 0) as $left
    | ($r[2] // 0) as $bottom
    | ($r[3] // 0) as $right
    | [
        ($x + $left),
        ($y + $top),
        ($logical_w - $left - $right),
        ($logical_h - $top - $bottom)
      ]
    | @tsv
' <<<"$monitor_json")"

if [[ "$mw" == "0" || "$mh" == "0" ]]; then
    exit 1
fi

target_w=$(( mw * 90 / 100 ))
target_h=$(( mh * 90 / 100 ))
target_x=$(( mx + (mw - target_w) / 2 ))
target_y=$(( my + (mh - target_h) / 2 ))

hyprctl dispatch setfloating "address:${address}" >/dev/null 2>&1 || true
hyprctl --batch \
    "dispatch movewindowpixel exact ${target_x} ${target_y},address:${address}; \
     dispatch resizewindowpixel exact ${target_w} ${target_h},address:${address}" >/dev/null 2>&1 || true
