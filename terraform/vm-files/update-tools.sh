#!/bin/bash
# update-tools.sh — Update/revert Claude Code and Codex CLI with version logging.
#
# Usage:
#   update-tools.sh all                    Update both tools to latest
#   update-tools.sh claude                 Update only Claude Code
#   update-tools.sh codex                  Update only Codex CLI
#   update-tools.sh claude --revert 1.2.3  Pin Claude to specific version
#   update-tools.sh codex  --revert 0.5.0  Pin Codex to specific version
#   update-tools.sh all    --log           Print update history for both tools

set -euo pipefail

LOG_DIR="${HOME}/.tool-updates"
mkdir -p "$LOG_DIR"

CLAUDE_PKG="@anthropic-ai/claude-code"
CODEX_PKG="@openai/codex"

get_version() {
    local pkg="$1"
    npm list -g "$pkg" --depth=0 2>/dev/null | grep "$pkg" | sed 's/.*@//' || echo "not-installed"
}

do_update() {
    local name="$1" pkg="$2"
    local logfile="$LOG_DIR/${name}.log"
    local before after

    before=$(get_version "$pkg")
    echo "==> Updating $name ($pkg) from $before..."
    sudo npm install -g "$pkg@latest" --loglevel=warn

    after=$(get_version "$pkg")
    if [ "$before" != "$after" ]; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') | $before -> $after" >> "$logfile"
        echo "==> $name updated: $before -> $after"
    else
        echo "==> $name already at latest: $after"
    fi
}

do_revert() {
    local name="$1" pkg="$2" version="$3"
    local logfile="$LOG_DIR/${name}.log"
    local before after

    before=$(get_version "$pkg")
    echo "==> Reverting $name ($pkg) to $version..."
    sudo npm install -g "$pkg@$version" --loglevel=warn

    after=$(get_version "$pkg")
    if [ "$before" != "$after" ]; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') | $before -> $after (revert)" >> "$logfile"
        echo "==> $name reverted: $before -> $after"
    else
        echo "==> $name already at $version"
    fi
}

show_log() {
    local name="$1"
    local logfile="$LOG_DIR/${name}.log"
    echo "--- $name update history (last 20) ---"
    if [ -f "$logfile" ]; then
        tail -20 "$logfile"
    else
        echo "  (no history)"
    fi
    echo ""
}

# --- Argument parsing ---

TOOL="${1:-}"
ACTION="${2:-}"
VERSION="${3:-}"

if [ -z "$TOOL" ]; then
    echo "Usage: update-tools.sh <all|claude|codex> [--revert <version>] [--log]"
    exit 1
fi

case "$TOOL" in
    all)
        if [ "$ACTION" = "--log" ]; then
            show_log "claude"
            show_log "codex"
        else
            do_update "claude" "$CLAUDE_PKG"
            do_update "codex"  "$CODEX_PKG"
        fi
        ;;
    claude)
        if [ "$ACTION" = "--revert" ]; then
            [ -z "$VERSION" ] && { echo "Usage: update-tools.sh claude --revert <version>"; exit 1; }
            do_revert "claude" "$CLAUDE_PKG" "$VERSION"
        elif [ "$ACTION" = "--log" ]; then
            show_log "claude"
        else
            do_update "claude" "$CLAUDE_PKG"
        fi
        ;;
    codex)
        if [ "$ACTION" = "--revert" ]; then
            [ -z "$VERSION" ] && { echo "Usage: update-tools.sh codex --revert <version>"; exit 1; }
            do_revert "codex" "$CODEX_PKG" "$VERSION"
        elif [ "$ACTION" = "--log" ]; then
            show_log "codex"
        else
            do_update "codex" "$CODEX_PKG"
        fi
        ;;
    *)
        echo "Unknown tool: $TOOL (use all, claude, or codex)"
        exit 1
        ;;
esac
