#!/usr/bin/env bash
# Genera AutoClick.app autocontenido y un .dmg "arrastrar a Applications" para macOS.
# Ejecutar en macOS: ./build_macos.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv311/bin/python"
[ -x "$PY" ] || PY=".venv/bin/python"

APP="dist/AutoClick.app"

echo ">>> PyInstaller (app bundle)..."
rm -rf "$APP"
"$PY" -m PyInstaller --noconfirm --clean --windowed --onedir --name AutoClick --specpath build main.py

[ -d "$APP" ] || { echo "No se genero $APP"; exit 1; }

echo ">>> Firma ad-hoc (obligatoria en Apple Silicon)..."
codesign --force --deep --sign - "$APP"

echo ">>> Creando .dmg..."
STAGE="dist/dmg-stage"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

DMG="dist/AutoClick-macos.dmg"
rm -f "$DMG"
hdiutil create -volname "AutoClick" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"

echo ">>> Listo: $DMG"
echo
echo "AVISO Gatekeeper: al bajar de internet, la primera apertura se hace con"
echo "clic derecho sobre AutoClick.app -> Abrir (o: xattr -cr /Applications/AutoClick.app)."
echo "Ademas, el usuario debe autorizar Accesibilidad en"
echo "Configuracion -> Privacidad y seguridad -> Accesibilidad."