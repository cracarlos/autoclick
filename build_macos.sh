#!/usr/bin/env bash
# Genera el binario de AutoClick y el .dmg para macOS.
# Ejecutar en macOS: ./build_macos.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv311/bin/python"
[ -x "$PY" ] || PY=".venv/bin/python"

echo ">>> PyInstaller (onefile)..."
"$PY" -m PyInstaller --noconfirm --clean AutoClick.spec

BIN="dist/AutoClick"
[ -f "$BIN" ] || { echo "No se encontro dist/AutoClick"; exit 1; }

echo ">>> Creando .dmg..."
DMG="dist/AutoClick-macos.dmg"
rm -f "$DMG"
hdiutil create -volname "AutoClick" -srcfolder "$BIN" -ov -format UDZO "$DMG"

echo ">>> Listo: $DMG"