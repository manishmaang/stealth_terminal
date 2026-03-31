import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk


class InputBar(Gtk.Box):
    def __init__(self, on_send):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.on_send = on_send
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.set_margin_bottom(4)
        self.set_margin_top(4)

        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_placeholder_text("Type a message...")
        self.entry.add_css_class("input-entry")
        self.entry.connect("activate", self._on_activate)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.entry.add_controller(key_controller)

        self.send_btn = Gtk.Button(label="Send")
        self.send_btn.add_css_class("send-button")
        self.send_btn.connect("clicked", self._on_activate)

        self.append(self.entry)
        self.append(self.send_btn)

    def _on_activate(self, *_args):
        text = self.entry.get_text().strip()
        if text:
            self.entry.set_text("")
            self.on_send(text)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.entry.set_text("")
            return True
        return False

    def set_sensitive_input(self, sensitive: bool):
        self.entry.set_sensitive(sensitive)
        self.send_btn.set_sensitive(sensitive)

    def grab_focus_input(self):
        self.entry.grab_focus()
