#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN not found. Set PYTHON_BIN to your Python 3 interpreter." >&2
  exit 1
fi

echo "================================================"
echo "Building Biometric Tools Manager for Linux..."
echo "================================================"
echo

echo "Cleaning old build artifacts..."
rm -rf dist build
rm -f BiometricToolsManager.spec Biometric.spec

echo "Installing Python dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pyinstaller
"$PYTHON_BIN" -m pip install pywebview pyzk pillow

echo "Running PyInstaller for desktop app..."
"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --windowed \
  --name "Biometric" \
  --icon bio.ico \
  --add-data "auriga.png:." \
  --add-data "auriga1.png:." \
  --add-data "biometric_web_app_fixed.py:." \
  --add-data "data_storage.py:." \
  --hidden-import=webview \
  --hidden-import=zk \
  --hidden-import=data_storage \
  desktop_app.py

echo "Running PyInstaller for background sync service..."
"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --noconsole \
  --name "background_sync_service" \
  background_sync_service.py


echo
ls -1 dist

echo
echo "Creating desktop shortcut..."

# Get the absolute path to the executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXE_PATH="$SCRIPT_DIR/dist/Biometric"
ICON_PATH="$SCRIPT_DIR/bio.ico"

# Create .desktop file
DESKTOP_FILE="$HOME/Desktop/Biometric-Tools-Manager.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Biometric Tools Manager
Comment=Manage biometric devices and sync attendance data
Exec=$EXE_PATH
Icon=$ICON_PATH
Terminal=false
Categories=Office;Utility;
StartupNotify=true
EOF

# Make the .desktop file executable
chmod +x "$DESKTOP_FILE"

# Also mark it as trusted (for some desktop environments)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

echo "✅ Desktop shortcut created: $DESKTOP_FILE"

echo "================================================"
echo "Build complete! Binaries are in the dist/ directory."
echo "Desktop shortcut created on your Desktop!"
echo "================================================"
