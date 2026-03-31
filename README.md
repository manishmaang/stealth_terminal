# Invisible Terminal

A stealth AI chat application for Linux that remains invisible to others during screen sharing on Zoom, Google Meet, or any video conferencing tool.

## The Problem

You're in a meeting, sharing your screen, and you need to quickly ask an AI something — look up a command, draft a response, get help with code. But everything on your screen is visible to everyone in the call. On Linux/Wayland, there is **no API to hide a window from screen capture** (unlike Windows which has `SetWindowDisplayAffinity`). Every pixel on your display gets captured and streamed.

## The Solution — Color Steganography

Invisible Terminal exploits a fundamental limitation of video compression.

### How Video Compression Works Against Screen Viewers

When you share your screen on Zoom or Google Meet, your display is captured and compressed using video codecs like H.264, VP8, or VP9. These codecs work by:

1. **Chroma subsampling (4:2:0)** — Color information is stored at half resolution. Subtle color differences are discarded.
2. **Quantization** — Similar pixel values are merged. At typical screen sharing bitrates (1-3 Mbps for 1080p), the codec cannot distinguish color values that are less than ~5-8 luma levels apart.
3. **Dark region compression** — Codecs allocate fewer bits to dark areas because human perception in video is less sensitive there.

### What This Means

- **Your physical monitor**: An IPS/OLED panel with 8-bit color can clearly distinguish `#000000` (pure black) from `#0A0A0A` (very dark gray). That's a 3.9% luminance difference — perceptible when you're sitting in front of the screen.
- **The compressed video stream**: At screen sharing bitrates, H.264 quantization merges `#000000` and `#0A0A0A` into the same value. The text becomes **literally invisible** in the video feed that other meeting participants see.

### The Result

You see the text clearly on your monitor. Everyone else in the meeting sees a plain black window — if they notice it at all.

## Features

### Stealth Mode (Default)
- Near-black text on pure black background
- Configurable text darkness level (0-30) — tune for your specific monitor
- Configurable window opacity (semi-transparent overlay)
- Scrollbar hidden in stealth mode (scrollbars are a visual giveaway)
- Blank window title

### Panic Hotkey
- **Ctrl+Shift+H** — Instantly hides the entire window with a global keyboard shortcut
- Works even when the window doesn't have focus
- Press again to bring it back
- Uses XDG GlobalShortcuts portal (Wayland-native) with D-Bus fallback

### Always-on-Top
- Window stays above all other windows like a sticky note
- Doesn't minimize when you click on your browser or IDE
- Resizable and draggable — position it wherever you want
- Close with the X button when done

### AI Chat
- **Ollama** — Chat with local models (llama3, mistral, codellama, etc.). No API key needed, fully offline.
- **Claude API** — Chat with Anthropic's Claude models. Requires API key.
- Streaming responses — text appears word by word as the AI generates it
- Switch between backends on the fly with the "Switch AI" button
- Full conversation context maintained

### Normal Mode
- Toggle stealth off with **Ctrl+S** for a standard dark-themed chat when not in a meeting
- Full-brightness colors for comfortable reading

## Installation

```bash
cd invisible-terminal
chmod +x install.sh
./install.sh
```

This creates a virtual environment, installs dependencies, and sets up the `exitt` command.

### Requirements
- **Linux** with Wayland + GNOME (tested on Ubuntu with GNOME 46+)
- **Python 3.11+**
- **GTK4 + libadwaita** (pre-installed on most GNOME desktops)
- **Ollama** (optional, for local AI) — [install from ollama.com](https://ollama.com)
- **Claude API key** (optional, for Claude) — set in config file

## Usage

### Launch
```bash
exitt
```
Run it from any terminal. The window appears as a transparent, always-on-top overlay.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+H` | Panic hide/show (global — works from any app) |
| `Ctrl+S` | Toggle stealth/normal mode |
| `Ctrl+Up` | Increase text darkness (more visible) |
| `Ctrl+Down` | Decrease text darkness (more hidden) |
| `Ctrl+L` | Clear chat history |
| `Ctrl+Q` | Quit |
| `Enter` | Send message |
| `Escape` | Clear input field |

### First-Time Setup

1. Run `exitt` to launch
2. The status bar shows `[S:10] Ollama (llama3)` — stealth mode, darkness 10, Ollama backend
3. Press **Ctrl+Up/Down** to calibrate darkness for your monitor:
   - Too low = you can't read the text yourself
   - Too high = visible in screen share
   - Sweet spot is usually **8-12** for most IPS monitors
4. Start a test Zoom/Meet call with yourself to verify invisibility

### Configuring Claude API

Edit `~/.config/invisible-terminal/config.toml`:

```toml
[ai]
backend = "claude"
claude_api_key = "sk-ant-..."
claude_model = "claude-sonnet-4-20250514"
```

Or keep `backend = "ollama"` and switch to Claude on the fly with the "Switch AI" button.

## Configuration

Config file location: `~/.config/invisible-terminal/config.toml`

```toml
[general]
stealth_mode = true        # Start in stealth mode
opacity = 0.85             # Window opacity (0.0 = fully transparent, 1.0 = opaque)
text_darkness = 10         # Text color value 0-30 (lower = more hidden)

[hotkey]
panic_key = "ctrl+shift+h" # Global panic hide/show shortcut

[ai]
backend = "ollama"                      # "ollama" or "claude"
ollama_model = "llama3"                 # Any model pulled in Ollama
ollama_url = "http://localhost:11434"   # Ollama API endpoint
claude_api_key = ""                     # Your Anthropic API key
claude_model = "claude-sonnet-4-20250514"  # Claude model to use

[ui]
font_family = "Monospace"  # Font for chat text
font_size = 13             # Font size in pixels
window_width = 500         # Default window width
window_height = 400        # Default window height
```

## How Effective Is the Stealth?

### What makes it invisible
- H.264/VP8/VP9 quantization at screen sharing bitrates (1-3 Mbps) merges color values within ~5-8 luma levels
- `#0A0A0A` on `#000000` is a difference of 10 luma levels — right at the destruction threshold
- Dark regions get fewer bits allocated, further degrading subtle differences
- Meeting platforms often reduce quality further during bandwidth fluctuations

### Limitations (be aware)
- **Monitor-dependent**: The sweet spot varies by monitor. OLED displays show the text more clearly than cheap TN panels. Calibrate with Ctrl+Up/Down.
- **Not 100% foolproof**: If someone records the meeting at very high bitrate and then cranks up brightness/contrast in post-processing, they could theoretically recover the text. This is unlikely in practice.
- **Bandwidth spikes**: If the connection is unusually good and the codec uses a very high bitrate, more color detail is preserved. The panic hotkey is your safety net.

### Defense layers
1. **Primary**: Color steganography (near-black text)
2. **Secondary**: Window transparency (blends with desktop behind it)
3. **Tertiary**: Panic hotkey (Ctrl+Shift+H) for instant hide

## Architecture

```
invisible_terminal/
    app.py          — GTK4/Adwaita application bootstrap, CSS provider, backend init
    window.py       — Main window: always-on-top, transparency, layout, keyboard shortcuts
    chat_view.py    — Scrollable message history with TextBuffer and colored tags
    input_bar.py    — Text input field with Enter-to-send
    stealth.py      — CSS generation engine for stealth/normal modes
    ai_backend.py   — Abstract AI backend + Ollama (HTTP) and Claude (SDK) implementations
    hotkey.py       — Global panic hotkey via XDG GlobalShortcuts portal + D-Bus fallback
    config.py       — TOML config loader/saver
```

### Streaming Architecture
```
User sends message
    → InputBar emits callback
    → Window spawns background thread
    → Thread calls ai_backend.stream_response() (generator)
    → Each text chunk: GLib.idle_add(chat_view.append_ai_chunk, chunk)
    → GTK main thread appends to TextBuffer + auto-scrolls
    → On completion: re-enable input, focus entry
```

## Troubleshooting

### "Cannot connect to AI backend"
- **Ollama**: Make sure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull llama3`)
- **Claude**: Check your API key in `~/.config/invisible-terminal/config.toml`

### Window doesn't stay on top
- This depends on your GNOME/Mutter version. Use the panic hotkey (Ctrl+Shift+H) to toggle visibility instead.

### Global hotkey not working
- The XDG GlobalShortcuts portal may show a confirmation dialog on first use — accept it
- Fallback: manually trigger via D-Bus:
  ```bash
  dbus-send --session --dest=com.invisible.terminal /com/invisible/terminal com.invisible.terminal.Toggle
  ```
  Bind this command to any key in GNOME Settings → Keyboard → Custom Shortcuts

### Text too hard to read / too visible
- Adjust with **Ctrl+Up** (brighter) or **Ctrl+Down** (darker)
- Edit `text_darkness` in config for a persistent default
- Test by sharing your screen in a Zoom call with yourself on another device

## License

MIT
