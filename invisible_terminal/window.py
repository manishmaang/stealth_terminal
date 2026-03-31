import threading

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib

from .chat_view import ChatView
from .input_bar import InputBar
from .ai_backend import AIBackend
from .stealth import generate_css, apply_css


class InvisibleWindow(Adw.ApplicationWindow):
    def __init__(self, app, config: dict, backend: AIBackend,
                 css_provider: Gtk.CssProvider):
        super().__init__(application=app)
        self.config = config
        self.backend = backend
        self.css_provider = css_provider
        self._messages = []
        self._stealth = config["general"]["stealth_mode"]
        self._darkness = config["general"]["text_darkness"]
        self._opacity = config["general"]["opacity"]
        self._streaming = False

        ui = config["ui"]
        self.set_default_size(ui["window_width"], ui["window_height"])
        self.set_title("")
        self.set_resizable(True)

        self._build_ui()
        self._setup_shortcuts()
        self._apply_stealth()

        self.connect("realize", self._on_realize)

    def _on_realize(self, widget):
        # Always-on-top: GTK4/GNOME honors this on Wayland
        surface = self.get_surface()
        if hasattr(surface, "set_keep_above"):
            surface.set_keep_above(True)

    def _build_ui(self):
        # Header bar - minimal
        header = Adw.HeaderBar()
        header.set_show_title(False)
        header.set_decoration_layout("close")

        # Status label showing current mode and backend
        self.status_label = Gtk.Label()
        self.status_label.add_css_class("status-label")
        self._update_status()
        header.pack_start(self.status_label)

        # Backend selector button
        backend_btn = Gtk.Button(label="Switch AI")
        backend_btn.add_css_class("model-selector")
        backend_btn.connect("clicked", self._on_switch_backend)
        header.pack_end(backend_btn)

        # Chat view
        self.chat_view = ChatView()

        # Input bar
        self.input_bar = InputBar(on_send=self._on_send)

        # Layout
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.add_css_class("chat-container")
        content_box.append(self.chat_view)
        content_box.append(self.input_bar)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header)
        main_box.append(content_box)

        self.set_content(main_box)

    def _setup_shortcuts(self):
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(controller)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        ctrl = state & Gdk.ModifierType.CONTROL_MASK

        if ctrl and keyval == Gdk.KEY_s:
            self._toggle_stealth()
            return True
        elif ctrl and keyval == Gdk.KEY_Up:
            self._adjust_darkness(1)
            return True
        elif ctrl and keyval == Gdk.KEY_Down:
            self._adjust_darkness(-1)
            return True
        elif ctrl and keyval == Gdk.KEY_q:
            self.close()
            return True
        elif ctrl and keyval == Gdk.KEY_l:
            self.chat_view.clear_history()
            self._messages.clear()
            return True
        return False

    def _toggle_stealth(self):
        self._stealth = not self._stealth
        self._apply_stealth()
        mode = "STEALTH" if self._stealth else "NORMAL"
        self.chat_view.append_system_message(f"Switched to {mode} mode")

    def _adjust_darkness(self, delta: int):
        self._darkness = max(1, min(30, self._darkness + delta))
        self._apply_stealth()
        self._update_status()

    def _apply_stealth(self):
        ui = self.config["ui"]
        css = generate_css(
            stealth=self._stealth,
            darkness=self._darkness,
            opacity=self._opacity,
            font_family=ui["font_family"],
            font_size=ui["font_size"],
        )
        apply_css(self.css_provider, css)
        self.chat_view.update_colors(self._stealth, self._darkness)
        self._update_status()

    def _update_status(self):
        mode = "S" if self._stealth else "N"
        self.status_label.set_text(
            f"[{mode}:{self._darkness}] {self.backend.name()}"
        )

    def _on_switch_backend(self, btn):
        # Emit signal for app to handle backend switching
        app = self.get_application()
        if hasattr(app, "switch_backend"):
            app.switch_backend()
            self._update_status()

    def _on_send(self, text: str):
        if self._streaming:
            return

        self.chat_view.append_user_message(text)
        self._messages.append({"role": "user", "content": text})
        self.input_bar.set_sensitive_input(False)
        self._streaming = True

        thread = threading.Thread(target=self._run_ai, daemon=True)
        thread.start()

    def _run_ai(self):
        GLib.idle_add(self.chat_view.start_ai_response)
        ai_text = ""

        try:
            for chunk in self.backend.stream_response(self._messages):
                ai_text += chunk
                GLib.idle_add(self.chat_view.append_ai_chunk, chunk)
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg:
                error_msg = f"Cannot connect to AI backend. Is it running? ({error_msg})"
            GLib.idle_add(self.chat_view.append_ai_chunk, f"\n[Error: {error_msg}]")

        if ai_text:
            self._messages.append({"role": "assistant", "content": ai_text})

        GLib.idle_add(self._finish_streaming)

    def _finish_streaming(self):
        self.chat_view.finalize_ai_response()
        self._streaming = False
        self.input_bar.set_sensitive_input(True)
        self.input_bar.grab_focus_input()

    def toggle_visibility(self, action="toggle"):
        if action == "hide" or (action == "toggle" and self.get_visible()):
            self.set_visible(False)
        else:
            self.set_visible(True)
            self.present()
