#!/usr/bin/env bash
# qylock launcher — session lock via Quickshell (ext-session-lock-v1)
# Never kill this process from outside; unlock only via password.

set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/qylock.log"

log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG_FILE" >&2; }

# Already locked — do not spawn a second lock client
if pgrep -f '[q]uickshell-lockscreen/lock_shell.qml' >/dev/null 2>&1; then
  log "qylock: lock already active, not starting another instance"
  exit 0
fi

export QML2_IMPORT_PATH="$DIR/imports:${QML2_IMPORT_PATH:-}"
export QML_XHR_ALLOW_FILE_READ=1
export XDG_SESSION_TYPE="${XDG_SESSION_TYPE:-wayland}"

CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/qylock/theme"
if [ -n "${1:-}" ]; then
  export QS_THEME="$1"
elif [ -f "$CONFIG_FILE" ]; then
  export QS_THEME="$(tr -d '[:space:]' < "$CONFIG_FILE")"
else
  export QS_THEME="material-you"
fi

if [ -d "$DIR/themes_link/$QS_THEME" ]; then
  export QS_THEME_PATH="$DIR/themes_link/$QS_THEME"
elif [ -d "$DIR/../themes/$QS_THEME" ]; then
  export QS_THEME_PATH="$DIR/../themes/$QS_THEME"
else
  log "qylock: theme not found: $QS_THEME"
  exit 1
fi

if [ ! -f "$QS_THEME_PATH/Main.qml" ]; then
  log "qylock: missing Main.qml in $QS_THEME_PATH"
  exit 1
fi

log "Locking with theme=$QS_THEME path=$QS_THEME_PATH"

# Enable restore so a dead lock client does not soft-brick the session
if command -v hyprctl >/dev/null 2>&1; then
  hyprctl eval 'hl.misc({ allow_session_lock_restore = true })' >/dev/null 2>&1 \
    || hyprctl keyword misc:allow_session_lock_restore true >/dev/null 2>&1 \
    || true
fi

# Only clear dedicated lockers — NEVER touch qs/caelestia, NEVER unlock-session here
killall -q hyprlock swaylock wlogout 2>/dev/null || true

QS_BIN="$(command -v quickshell || command -v qs || true)"
if [ -z "$QS_BIN" ]; then
  log "qylock: quickshell/qs not found"
  exit 1
fi

log "exec $QS_BIN -p $DIR/lock_shell.qml"
exec "$QS_BIN" -p "$DIR/lock_shell.qml"
