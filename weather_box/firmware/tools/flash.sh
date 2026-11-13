#!/bin/sh
# Upload an already-compiled sketch to the XIAO ESP32-C3. Upload only, no compile.
# Installed as ~/.local/bin/fridge-flash. Usage: fridge-flash [sketch]   (default: fridge_4in26)
# Compile first with --build-path firmware/build/<sketch> (see CLAUDE.md).
set -eu

SKETCH="${1:-fridge_4in26}"
case "$SKETCH" in ''|*[!a-z0-9_]*) echo "bad sketch name: $SKETCH" >&2; exit 2 ;; esac

ROOT="$HOME/projects/hardware/weather_box"
BUILD="$ROOT/firmware/build/$SKETCH"
CLI="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
FQBN="esp32:esp32:XIAO_ESP32C3:PartitionScheme=huge_app"

[ -f "$BUILD/$SKETCH.ino.bin" ] || { echo "no build in $BUILD; compile first" >&2; exit 1; }

# The board's USB port disappears during deep sleep, so wait up to 90 s for it.
i=0
while :; do
  PORT="$(ls /dev/cu.usbmodem* 2>/dev/null | head -n 1 || true)"
  [ -n "$PORT" ] && break
  i=$((i + 1))
  [ "$i" -ge 90 ] && { echo "no XIAO port; hold B, tap R, release B" >&2; exit 1; }
  sleep 1
done

echo "Uploading $SKETCH to $PORT"
exec "$CLI" upload -p "$PORT" --input-dir "$BUILD" --fqbn "$FQBN" "$ROOT/firmware/$SKETCH"
