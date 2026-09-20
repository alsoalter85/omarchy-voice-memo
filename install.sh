#!/usr/bin/env bash
# voice-memo installer: links the script into ~/.local/bin and checks dependencies.
set -euo pipefail

cd "$(dirname "$0")"

missing=0
for cmd in pw-record ffmpeg ffprobe wl-copy omarchy flock numfmt setsid mktemp wtype; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "missing dependency: $cmd"
    missing=1
  fi
done
[[ $missing -eq 0 ]] || { echo "Install the missing tools and re-run."; exit 1; }

if command -v voxtype >/dev/null 2>&1; then
  echo "voxtype found — transcription enabled."
else
  echo "note: voxtype not found — install with 'omarchy voxtype install' for transcription."
  echo "      (voice-memo still works; clipboard falls back to the MP3 file reference)"
fi

mkdir -p "$HOME/.local/bin"
ln -sf "$PWD/voice-memo" "$HOME/.local/bin/voice-memo"
chmod +x "$PWD/voice-memo"
echo "Installed: ~/.local/bin/voice-memo -> $PWD/voice-memo"

if [[ ! -f "$HOME/.config/voice-memo/replacements" ]]; then
  mkdir -p "$HOME/.config/voice-memo"
  cp replacements.example "$HOME/.config/voice-memo/replacements"
  echo "Seeded ~/.config/voice-memo/replacements — edit to add your own terms"
fi

if ! grep -q "voice-memo" "$HOME/.config/hypr/bindings.lua" 2>/dev/null; then
  cat <<'EOF'

Add the bindings to ~/.config/hypr/bindings.lua:

    -- Toggle recording.
    o.bind("SUPER + SHIFT + R", "Voice memo", "voice-memo")

    -- ESC-to-trash: consuming bind, armed only while recording.
    voice_memo_esc = hl.bind("ESCAPE", hl.dsp.exec_cmd("voice-memo cancel"),
      { description = "Voice memo: trash take" })
    voice_memo_esc:set_enabled(false)

Hyprland reloads automatically on save. Validate with: hyprctl configerrors
EOF
else
  echo "Keybinding already present in ~/.config/hypr/bindings.lua"
fi
