#!/usr/bin/env bash
# ============================================================================
# Linux systemd Service Setup for Biometric Background Sync Service
# ============================================================================
# This script is the Linux equivalent of setup_windows_task.bat.
# It creates a systemd user service that:
#   - Runs the background_sync_service on boot / login
#   - Restarts automatically if it crashes
#   - Can be managed with standard systemctl commands
# ============================================================================

set -euo pipefail

SERVICE_NAME="biometric-background-sync"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXE_PATH="$SCRIPT_DIR/dist/background_sync_service"
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
LOG_DIR="$HOME/.local/share/biometric_tools"

# ─── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

echo "================================================"
echo " Biometric Background Sync — Linux Service Setup"
echo "================================================"
echo

# ─── Menu ────────────────────────────────────────────────────────────────────
echo "Select an action:"
echo ""
echo "  1. Install / update service (default: every 5 minutes)"
echo "  2. Install / update service with custom interval"
echo "  3. Start the service now"
echo "  4. Stop the service"
echo "  5. Restart the service"
echo "  6. Check service status"
echo "  7. View latest logs"
echo "  8. Remove / uninstall service"
echo ""
read -rp "Enter choice [1-8]: " CHOICE

# ─── Helper: require the compiled executable ──────────────────────────────────
require_exe() {
    if [[ ! -f "$EXE_PATH" ]]; then
        error "Executable not found: $EXE_PATH"
        error "Please run ./build_linux.sh first to compile the application."
        exit 1
    fi
}

# ─── Helper: write the systemd unit file ─────────────────────────────────────
write_service_unit() {
    local interval_min="${1:-5}"

    mkdir -p "$HOME/.config/systemd/user"
    mkdir -p "$LOG_DIR"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Biometric Background Sync Service
Documentation=file://${SCRIPT_DIR}/BACKGROUND_SERVICE_SETUP.md
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=${EXE_PATH} --force
Restart=always
RestartSec=${interval_min}m
WorkingDirectory=${SCRIPT_DIR}/dist
Environment=HOME=${HOME}
StandardOutput=append:${LOG_DIR}/auto_sync_service.log
StandardError=append:${LOG_DIR}/auto_sync_service.log

[Install]
WantedBy=default.target
EOF

    info "Service unit written to: $SERVICE_FILE"
}

# ─── Actions ─────────────────────────────────────────────────────────────────

case "$CHOICE" in

  1)
    require_exe
    INTERVAL=5
    info "Installing service with default interval: every ${INTERVAL} minute(s)…"
    write_service_unit "$INTERVAL"
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVICE_NAME"
    echo
    info "✅  Service installed and started!"
    info "    It will restart every ${INTERVAL} minutes and survive reboots."
    ;;

  2)
    require_exe
    echo ""
    echo "Select interval:"
    echo "  1.  Every  1 minute"
    echo "  2.  Every  5 minutes  (Recommended)"
    echo "  3.  Every 10 minutes"
    echo "  4.  Every 15 minutes"
    echo "  5.  Every 30 minutes"
    echo "  6.  Every 60 minutes"
    echo "  7.  Custom (enter minutes manually)"
    echo ""
    read -rp "Enter choice [1-7]: " INT_CHOICE

    case "$INT_CHOICE" in
      1) INTERVAL=1 ;;
      2) INTERVAL=5 ;;
      3) INTERVAL=10 ;;
      4) INTERVAL=15 ;;
      5) INTERVAL=30 ;;
      6) INTERVAL=60 ;;
      7) read -rp "Enter interval in minutes: " INTERVAL ;;
      *) warn "Invalid choice, using 5 minutes."; INTERVAL=5 ;;
    esac

    info "Installing service with interval: every ${INTERVAL} minute(s)…"
    write_service_unit "$INTERVAL"
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVICE_NAME"
    echo
    info "✅  Service installed and started!"
    info "    Sync interval: every ${INTERVAL} minute(s)."
    ;;

  3)
    info "Starting service…"
    systemctl --user start "$SERVICE_NAME"
    systemctl --user status "$SERVICE_NAME" --no-pager
    ;;

  4)
    info "Stopping service…"
    systemctl --user stop "$SERVICE_NAME"
    info "Service stopped."
    ;;

  5)
    info "Restarting service…"
    systemctl --user restart "$SERVICE_NAME"
    systemctl --user status "$SERVICE_NAME" --no-pager
    ;;

  6)
    echo ""
    systemctl --user status "$SERVICE_NAME" --no-pager
    ;;

  7)
    LOG_FILE="$LOG_DIR/auto_sync_service.log"
    if [[ -f "$LOG_FILE" ]]; then
        echo ""
        info "Last 50 lines of $LOG_FILE:"
        tail -50 "$LOG_FILE"
    else
        warn "Log file not found at $LOG_FILE"
        info "Showing journald logs instead:"
        journalctl --user -u "$SERVICE_NAME" -n 50 --no-pager
    fi
    ;;

  8)
    warn "Removing service '${SERVICE_NAME}'…"
    systemctl --user stop "$SERVICE_NAME"  2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user daemon-reload
    rm -f "$SERVICE_FILE"
    info "✅  Service removed successfully."
    ;;

  *)
    error "Invalid choice: $CHOICE"
    exit 1
    ;;

esac

echo ""
echo "================================================"
echo " Management commands:"
echo "   systemctl --user start   $SERVICE_NAME"
echo "   systemctl --user stop    $SERVICE_NAME"
echo "   systemctl --user restart $SERVICE_NAME"
echo "   systemctl --user status  $SERVICE_NAME"
echo "   journalctl --user -u     $SERVICE_NAME -f"
echo "================================================"
