import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Pango


class ChatView(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.add_css_class("chat-view")
        self.textview.set_left_margin(4)
        self.textview.set_right_margin(4)
        self.textview.set_top_margin(4)
        self.textview.set_bottom_margin(4)

        self.buffer = self.textview.get_buffer()

        # Tags with direct foreground colors (updated by update_colors)
        self.tag_user = self.buffer.create_tag("user", weight=Pango.Weight.BOLD)
        self.tag_ai = self.buffer.create_tag("ai")
        self.tag_system = self.buffer.create_tag("system",
                                                  style=Pango.Style.ITALIC)

        self.set_child(self.textview)
        self._streaming = False

    def update_colors(self, stealth: bool, darkness: int):
        if stealth:
            user_val = min(darkness + 5, 30)
            ai_val = darkness
            sys_val = min(darkness + 3, 25)
        else:
            user_val, ai_val, sys_val = None, None, None

        for tag, val, fallback in [
            (self.tag_user, user_val, "#8bc6fc"),
            (self.tag_ai, ai_val, "#e0e0e0"),
            (self.tag_system, sys_val, "#888888"),
        ]:
            if stealth:
                rgba = Gdk.RGBA()
                rgba.parse(f"#{val:02x}{val:02x}{val:02x}")
                tag.set_property("foreground-rgba", rgba)
            else:
                rgba = Gdk.RGBA()
                rgba.parse(fallback)
                tag.set_property("foreground-rgba", rgba)

    def append_user_message(self, text: str):
        end_iter = self.buffer.get_end_iter()
        if self.buffer.get_char_count() > 0:
            self.buffer.insert(end_iter, "\n")
            end_iter = self.buffer.get_end_iter()
        self.buffer.insert_with_tags(end_iter, f"You: {text}\n", self.tag_user)
        self._scroll_to_bottom()

    def start_ai_response(self):
        self._streaming = True
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert_with_tags(end_iter, "AI: ", self.tag_ai)
        self._scroll_to_bottom()

    def append_ai_chunk(self, text: str):
        if not self._streaming:
            return
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert_with_tags(end_iter, text, self.tag_ai)
        self._scroll_to_bottom()

    def finalize_ai_response(self):
        self._streaming = False
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, "\n")
        self._scroll_to_bottom()

    def append_system_message(self, text: str):
        end_iter = self.buffer.get_end_iter()
        if self.buffer.get_char_count() > 0:
            self.buffer.insert(end_iter, "\n")
            end_iter = self.buffer.get_end_iter()
        self.buffer.insert_with_tags(end_iter, f"[{text}]\n", self.tag_system)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        GLib.idle_add(self._do_scroll)

    def _do_scroll(self):
        end_mark = self.buffer.get_insert()
        end_iter = self.buffer.get_end_iter()
        self.buffer.place_cursor(end_iter)
        self.textview.scroll_mark_onscreen(end_mark)
        return False

    def clear_history(self):
        self.buffer.set_text("")
