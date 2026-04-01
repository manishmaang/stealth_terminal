import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "invisible-terminal"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "general": {
        "stealth_mode": True,
        "opacity": 0.85,
        "text_darkness": 18,
    },
    "hotkey": {
        "panic_key": "ctrl+shift+h",
    },
    "ai": {
        "backend": "ollama",
        "ollama_model": "llama3",
        "ollama_url": "http://localhost:11434",
        "claude_api_key": "",
        "claude_model": "claude-sonnet-4-20250514",
    },
    "ui": {
        "font_family": "Monospace",
        "font_size": 13,
        "window_width": 500,
        "window_height": 400,
    },
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            user_config = tomllib.load(f)
        config = {}
        for section, defaults in DEFAULTS.items():
            config[section] = {**defaults, **user_config.get(section, {})}
        return config
    else:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULTS)
        return {s: {**v} for s, v in DEFAULTS.items()}


def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for section, values in config.items():
        lines.append(f"[{section}]")
        for key, val in values.items():
            if isinstance(val, bool):
                lines.append(f"{key} = {'true' if val else 'false'}")
            elif isinstance(val, str):
                lines.append(f'{key} = "{val}"')
            elif isinstance(val, (int, float)):
                lines.append(f"{key} = {val}")
        lines.append("")
    CONFIG_FILE.write_text("\n".join(lines))
