#!/usr/bin/env bash
# Renders the reel in parallel segments, joins them and muxes the narration.
# Usage: ./render-parallel.sh <narration.mp4> [out.mp4] [segments] [--wide]
set -euo pipefail
cd "$(dirname "$0")"
AUDIO="$1"; OUT="${2:-claude_edit_reel_red.mp4}"; N="${3:-3}"; EXTRA="${4:-}"
TOTAL=$(node -e "console.log(Math.round(77.485 * 30))")
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
for i in $(seq 0 $((N - 1))); do
  A=$((TOTAL * i / N)); B=$((TOTAL * (i + 1) / N))
  node render.mjs --range "$A:$B" "$TMP/seg$i.mp4" $EXTRA &
done
wait
for i in $(seq 0 $((N - 1))); do echo "file '$TMP/seg$i.mp4'"; done > "$TMP/list.txt"
ffmpeg -y -v error -f concat -safe 0 -i "$TMP/list.txt" -i "$AUDIO" -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
