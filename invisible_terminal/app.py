import sys

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib

from .config import load_config, save_config
from .stealth import generate_css, apply_css
from .ai_backend import create_backend, OllamaBackend, ClaudeBackend
from .window import InvisibleWindow
from .hotkey import PanicHotkey


class InvisibleTerminalApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.invisible.terminal",
                         flags=0)
        self.config = load_config()
        self.css_provider = Gtk.CssProvider()
        self.win = None
        self.hotkey = None
        self.backend = None
        self._current_backend_type = self.config["ai"]["backend"]

    def do_activate(self):
        if self.win is not None:
            self.win.present()
            return

        # Force dark theme
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        # Apply CSS globally
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Create AI backend
        try:
            self.backend = create_backend(self.config)
        except ValueError as e:
            print(f"[warning] {e}")
            print("[info] Falling back to Ollama backend")
            self.config["ai"]["backend"] = "ollama"
            self._current_backend_type = "ollama"
            self.backend = create_backend(self.config)

        # Create window
        self.win = InvisibleWindow(
            app=self,
            config=self.config,
            backend=self.backend,
            css_provider=self.css_provider,
        )

        # Welcome message
        self.win.chat_view.append_system_message(
            f"Invisible Terminal ready | Backend: {self.backend.name()}"
        )
        self.win.chat_view.append_system_message(
            "Ctrl+S: toggle stealth | Ctrl+Up/Down: adjust darkness | "
            "Ctrl+L: clear | Ctrl+Q: quit"
        )

        self.win.present()
        self.win.input_bar.grab_focus_input()

        # Register panic hotkey
        self.hotkey = PanicHotkey(on_activate=self._on_hotkey)
        self.hotkey.register_portal_shortcut()

    def _on_hotkey(self, action="toggle"):
        if self.win:
            self.win.toggle_visibility(action)

    def switch_backend(self):
        if self._current_backend_type == "ollama":
            api_key = self.config["ai"].get("claude_api_key", "")
            if not api_key:
                self.win.chat_view.append_system_message(
                    "Claude API key not configured. Edit ~/.config/invisible-terminal/config.toml"
                )
                return
            self._current_backend_type = "claude"
            self.config["ai"]["backend"] = "claude"
        else:
            self._current_backend_type = "ollama"
            self.config["ai"]["backend"] = "ollama"

        try:
            self.backend = create_backend(self.config)
            self.win.backend = self.backend
            self.win.chat_view.append_system_message(
                f"Switched to {self.backend.name()}"
            )
        except Exception as e:
            self.win.chat_view.append_system_message(f"Backend switch failed: {e}")

    def do_shutdown(self):
        if self.hotkey:
            self.hotkey.cleanup()
        Adw.Application.do_shutdown(self)


def main():
    app = InvisibleTerminalApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
