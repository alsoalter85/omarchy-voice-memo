# voice-memo

One-hotkey voice memos for Omarchy / Hyprland. Press once to start recording,
press again to stop — you get an MP3 in `~/Recordings/` and a file reference on
the clipboard, ready to paste into Slack, a browser upload, or a file manager.

![mockup](mockup/voice-memo-mockup.png)

## Usage

| Press | What happens |
|---|---|
| `SUPER+SHIFT+R` (1st) | Recording starts from the default mic; a persistent critical notification shows **● Recording…** |
| `SUPER+SHIFT+R` (2nd) | Recording stops, WAV → MP3 (`~/Recordings/voice-<timestamp>.mp3`), WAV deleted, clipboard gets a `text/uri-list` file reference, notification swaps to **Voice memo saved** |

Recordings live **only** in `~/Recordings/` (nothing in `/tmp` survives a reboot — this keeps them).

## Install

```bash
./install.sh
```

This symlinks `voice-memo` into `~/.local/bin` and checks dependencies.
Then add the binding to `~/.config/hypr/bindings.lua` (installer reminds you):

```lua
o.bind("SUPER + SHIFT + R", "Voice memo", "voice-memo")
```

Hyprland auto-reloads on save; verify with `hyprctl configerrors`.

## Dependencies

All stock on Omarchy: `pw-record` (PipeWire), `ffmpeg`, `wl-copy` (wl-clipboard), `omarchy` (notifications).

## How it works

- **Toggle script**: state file in `$XDG_RUNTIME_DIR` holds `<pid> <wav-path>`; presence of the file means "recording". An `flock` serializes rapid key presses.
- **Clean WAV**: recorder is stopped with `SIGINT` so `pw-record` finalizes the WAV header before exit.
- **Indicator**: `omarchy notification send -r 4210` — a fixed replace-id, so the "saved" notification swaps in place instead of stacking. `-t 0` keeps it on screen while recording.
- **Clipboard**: `wl-copy -t text/uri-list` with a `file://` URI, so paste targets treat it as a file attachment rather than raw audio bytes.
- **Encoding**: `ffmpeg -codec:a libmp3lame -q:a 4` (VBR ~165 kbps).

## Configuration

- `VOICE_MEMO_DIR` env var overrides `~/Recordings`.

## Mockup

`mockup/voice-memo-mockup.html` is the interactive design mockup (open in a browser).
