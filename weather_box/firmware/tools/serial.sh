#!/bin/sh
# Print the XIAO's serial log for a while (read only). Usage: fridge-serial [seconds]   (default 90)
# The USB port vanishes while the board deep-sleeps, so this reconnects each time it wakes.
set -eu

SECS="${1:-90}"
case "$SECS" in ''|*[!0-9]*) echo "seconds must be a number" >&2; exit 2 ;; esac

END=$(( $(date +%s) + SECS ))
while [ "$(date +%s)" -lt "$END" ]; do
  PORT="$(ls /dev/cu.usbmodem* 2>/dev/null | head -n 1 || true)"
  if [ -z "$PORT" ]; then sleep 0.5; continue; fi
  echo "--- connected to $PORT ---"
  stty -f "$PORT" 115200 raw -echo 2>/dev/null || { sleep 0.5; continue; }
  cat "$PORT" &
  PID=$!
  # Stop reading when time runs out or the port disappears (board went to sleep).
  while kill -0 "$PID" 2>/dev/null && [ -e "$PORT" ] && [ "$(date +%s)" -lt "$END" ]; do sleep 0.5; done
  kill "$PID" 2>/dev/null || true
  wait "$PID" 2>/dev/null || true
  sleep 1
done
echo "--- done ---"
