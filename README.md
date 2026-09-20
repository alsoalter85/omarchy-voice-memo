# voice-memo

One-hotkey voice memos for Omarchy / Hyprland, with **local transcription**.
Press once to start recording, press again to stop — you get an MP3 plus a
transcribed `.txt` in `~/Recordings/`, and the transcript text on the clipboard,
ready to paste anywhere. Transcription runs fully offline via
[voxtype](https://github.com/peteonrails/voxtype) (whisper.cpp).

## Usage

| Press | What happens |
|---|---|
| `SUPER+SHIFT+R` (1st) | Recording starts from the default mic; a persistent critical notification shows **● Recording…** |
| `SUPER+SHIFT+R` (2nd) | Recording stops → MP3 (`~/Recordings/voice-<timestamp>.mp3`) → **clipboard gets the file reference immediately** → local transcription → transcript saved as `.txt` next to the MP3, **clipboard is replaced with the transcript text**, and the transcript is **auto-pasted into the focused window**; notification swaps to **Voice memo saved** with a text preview |
| `ESC` (while recording) | Trashes the take to `/tmp/recordings-trashed/` (MP3 kept, no transcript, clipboard untouched). A consuming keybind is armed only while recording, so ESC never reaches the focused app mid-take — and behaves completely normally the rest of the time |

Auto-paste uses `wtype` with `ctrl+v` by default. Terminals don't paste on
`ctrl+v` — set `VOICE_MEMO_PASTE_KEYS="ctrl+shift+v"` if you mostly paste into a
terminal. Disable with `VOICE_MEMO_AUTOPASTE=0`.

So the clipboard is two-stage: paste right away for the MP3 file, or wait ~1–2s
(after the "Transcribing…" swap) and paste the text. If transcription fails or no
speech is detected, the clipboard simply keeps the file reference.

Recordings live **only** in `~/Recordings/` (nothing in `/tmp` survives a reboot — this keeps them).

## Install

```bash
./install.sh
```

This symlinks `voice-memo` into `~/.local/bin` and checks dependencies.
Then add the bindings to `~/.config/hypr/bindings.lua` (installer reminds you):

```lua
-- Toggle recording.
o.bind("SUPER + SHIFT + R", "Voice memo", "voice-memo")

-- ESC-to-trash: consuming bind, armed only while recording (see "How it works").
voice_memo_esc = hl.bind("ESCAPE", hl.dsp.exec_cmd("voice-memo cancel"),
  { description = "Voice memo: trash take" })
voice_memo_esc:set_enabled(false)
```

Hyprland auto-reloads on save; verify with `hyprctl configerrors`.

## Dependencies

All stock on Omarchy: `pw-record` (PipeWire), `ffmpeg`, `wl-copy` (wl-clipboard), `omarchy` (notifications), `wtype` (auto-paste).
Transcription: `voxtype` (`omarchy voxtype install`).

### Transcription engine

Model and language are voxtype's own settings (`~/.config/voxtype/config.toml` or
`voxtype configure`). Default is the `base` whisper model with `language = "auto"`
(Italian, English, … are auto-detected). For better accuracy at the cost of speed,
download a bigger model, e.g. `small` or `large-v3-turbo`, and set `model = "small"`.

## How it works

- **Toggle script**: state file in `$XDG_RUNTIME_DIR` holds `<pid> <wav-path>`; presence of the file means "recording". An `flock` serializes rapid key presses.
- **Clean WAV**: recorder is stopped with `SIGINT` so `pw-record` finalizes the WAV header before exit.
- **Indicator**: `omarchy notification send -r 4210` — a fixed replace-id, so the "saved"/"transcribing" notifications swap in place instead of stacking. `-t 0` keeps it on screen while recording.
- **Transcription**: MP3 → 16 kHz mono WAV (what whisper wants) → `voxtype -q transcribe`; stdout noise lines are filtered, the rest is the transcript.
- **Clipboard**: two-stage — `text/uri-list` file reference the moment the MP3 exists, then replaced by the transcript text when transcription finishes (`VOICE_MEMO_CLIPBOARD=file` keeps the file reference).
- **Auto-paste**: after the transcript lands on the clipboard, `wtype` injects the paste combo into the focused window.
- **Trash**: `voice-memo cancel` stops the recorder and encodes the take to the trash dir instead of `~/Recordings`, skipping transcription and clipboard. It's wired to ESC via a consuming Hyprland bind (defined in `bindings.lua`, disabled at load) that the script arms on record start and disarms on stop via `hyprctl eval 'voice_memo_esc:set_enabled(...)'` — so ESC is modal: captured only while a take is live, passed through otherwise.
- **Encoding**: `ffmpeg -codec:a libmp3lame -q:a 4` (VBR ~165 kbps).

## Custom vocabulary

Two layers, since whisper doesn't learn on its own:

1. **Bias (prevention)** — `initial_prompt` in `~/.config/voxtype/config.toml` primes the
   model with your terms, e.g. `initial_prompt = "Scalestack, Alessandro."`, so names and
   brand words are spelled right the first time. Also improves punctuation.
2. **Correction (guaranteed)** — `~/.config/voice-memo/replacements`, one `heard = replacement`
   per line, applied case-insensitively to every transcript (see `replacements.example`).
   This lives in voice-memo because voxtype's own `text.replacements` only runs in its
   dictation daemon — `voxtype transcribe` bypasses it.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `VOICE_MEMO_DIR` | `~/Recordings` | Output directory |
| `VOICE_MEMO_TRANSCRIBE` | `1` | `0` disables transcription |
| `VOICE_MEMO_CLIPBOARD` | `text` | `text` = transcript, `file` = MP3 file reference |
| `VOICE_MEMO_AUTOPASTE` | `1` | `0` disables auto-pasting the transcript into the focused window |
| `VOICE_MEMO_PASTE_KEYS` | `ctrl+v` | Auto-paste combo (`+`-joined modifiers + key); terminals usually need `ctrl+shift+v` |
| `VOICE_MEMO_TRASH_DIR` | `/tmp/recordings-trashed` | Where ESC-trashed takes are saved (auto-empties on reboot) |
