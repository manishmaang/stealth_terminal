import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib


class PanicHotkey:
    """Global panic hotkey using GNOME Shell GrabAccelerator D-Bus API.

    This is the native GNOME way to register global keyboard shortcuts.
    Falls back to a D-Bus service that can be triggered externally via:
        dbus-send --session --dest=com.invisible.terminal \
            /com/invisible/terminal com.invisible.terminal.Toggle
    """

    def __init__(self, on_activate):
        self.on_activate = on_activate
        self._action_id = 0
        self._signal_sub_id = 0
        self._dbus_owner_id = 0
        self._bus = None
        self._setup_dbus_service()

    def _setup_dbus_service(self):
        introspection_xml = """
        <node>
          <interface name="com.invisible.terminal">
            <method name="Toggle"/>
            <method name="Hide"/>
            <method name="Show"/>
          </interface>
        </node>
        """
        node_info = Gio.DBusNodeInfo.new_for_xml(introspection_xml)
        self._dbus_owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            "com.invisible.terminal",
            Gio.BusNameOwnerFlags.NONE,
            self._on_bus_acquired,
            None,
            None,
        )
        self._node_info = node_info

    def _on_bus_acquired(self, connection, name):
        connection.register_object(
            "/com/invisible/terminal",
            self._node_info.interfaces[0],
            self._on_dbus_method_call,
        )

    def _on_dbus_method_call(self, connection, sender, object_path,
                              interface_name, method_name, parameters,
                              invocation):
        if method_name in ("Toggle", "Hide", "Show"):
            GLib.idle_add(self.on_activate, method_name.lower())
        invocation.return_value(None)

    def register(self):
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION)

            # Subscribe to AcceleratorActivated signal first
            self._signal_sub_id = self._bus.signal_subscribe(
                "org.gnome.Shell",
                "org.gnome.Shell",
                "AcceleratorActivated",
                "/org/gnome/Shell",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_accelerator_activated,
            )

            # Grab Ctrl+Shift+H globally via GNOME Shell
            # modeFlags: 0 = normal mode, grabFlags: 0 = none
            result = self._bus.call_sync(
                "org.gnome.Shell",
                "/org/gnome/Shell",
                "org.gnome.Shell",
                "GrabAccelerator",
                GLib.Variant("(suu)", ("<Ctrl><Shift>h", 0, 0)),
                GLib.VariantType("(u)"),
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
            self._action_id = result.unpack()[0]
            if self._action_id > 0:
                print("[hotkey] Ctrl+Shift+H registered (GNOME Shell accelerator)")
            else:
                print("[hotkey] Accelerator grab returned 0, may not work")
        except Exception as e:
            print(f"[hotkey] Could not register global shortcut: {e}")
            print("[hotkey] Fallback: dbus-send --session "
                  "--dest=com.invisible.terminal "
                  "/com/invisible/terminal com.invisible.terminal.Toggle")

    def _on_accelerator_activated(self, connection, sender, path, iface,
                                   signal, params):
        action_id = params[0]
        if action_id == self._action_id:
            GLib.idle_add(self.on_activate, "toggle")

    def cleanup(self):
        if self._bus and self._action_id > 0:
            try:
                self._bus.call_sync(
                    "org.gnome.Shell",
                    "/org/gnome/Shell",
                    "org.gnome.Shell",
                    "UngrabAccelerator",
                    GLib.Variant("(u)", (self._action_id,)),
                    GLib.VariantType("(b)"),
                    Gio.DBusCallFlags.NONE,
                    5000,
                    None,
                )
            except Exception:
                pass
        if self._bus and self._signal_sub_id:
            self._bus.signal_unsubscribe(self._signal_sub_id)
        if self._dbus_owner_id:
            Gio.bus_unown_name(self._dbus_owner_id)
