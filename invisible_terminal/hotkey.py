import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib

PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
GLOBAL_SHORTCUTS_IFACE = "org.freedesktop.portal.GlobalShortcuts"


class PanicHotkey:
    """Global panic hotkey using XDG GlobalShortcuts portal.

    Falls back to a simple D-Bus service that can be triggered externally
    via: dbus-send --session --dest=com.invisible.terminal \
         /com/invisible/terminal com.invisible.terminal.Toggle
    """

    def __init__(self, on_activate):
        self.on_activate = on_activate
        self._session_path = None
        self._portal_working = False
        self._dbus_owner_id = 0
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

    def register_portal_shortcut(self):
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION)
            bus.call(
                PORTAL_BUS_NAME,
                PORTAL_OBJECT_PATH,
                GLOBAL_SHORTCUTS_IFACE,
                "CreateSession",
                GLib.Variant("(a{sv})", [{}]),
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,
                self._on_session_created,
            )
        except Exception as e:
            print(f"[hotkey] Portal shortcut unavailable: {e}")
            print("[hotkey] Use D-Bus fallback: dbus-send --session "
                  "--dest=com.invisible.terminal "
                  "/com/invisible/terminal com.invisible.terminal.Toggle")

    def _on_session_created(self, bus, result):
        try:
            res = bus.call_finish(result)
            response = res.unpack()
            if isinstance(response, tuple) and len(response) > 0:
                results = response[0] if isinstance(response[0], dict) else {}
                self._session_path = results.get("session_handle", "")

            if self._session_path:
                shortcuts = GLib.Variant("a(sa{sv})", [
                    ("panic-hide", {
                        "description": GLib.Variant("s", "Toggle Invisible Terminal"),
                        "preferred_trigger": GLib.Variant("s", "CTRL+SHIFT+H"),
                    }),
                ])
                bus.call(
                    PORTAL_BUS_NAME,
                    PORTAL_OBJECT_PATH,
                    GLOBAL_SHORTCUTS_IFACE,
                    "BindShortcuts",
                    GLib.Variant("(oa(sa{sv})sa{sv})", [
                        self._session_path,
                        [("panic-hide", {
                            "description": GLib.Variant("s", "Toggle Invisible Terminal"),
                            "preferred_trigger": GLib.Variant("s", "CTRL+SHIFT+H"),
                        })],
                        "",
                        {},
                    ]),
                    None,
                    Gio.DBusCallFlags.NONE,
                    5000,
                    None,
                    self._on_shortcuts_bound,
                )
        except Exception as e:
            print(f"[hotkey] Session creation failed: {e}")

    def _on_shortcuts_bound(self, bus, result):
        try:
            bus.call_finish(result)
            self._portal_working = True

            bus.signal_subscribe(
                PORTAL_BUS_NAME,
                GLOBAL_SHORTCUTS_IFACE,
                "Activated",
                self._session_path,
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_shortcut_activated,
            )
            print("[hotkey] Global shortcut Ctrl+Shift+H registered via portal")
        except Exception as e:
            print(f"[hotkey] Shortcut binding failed: {e}")

    def _on_shortcut_activated(self, connection, sender, path, iface,
                                signal, params):
        GLib.idle_add(self.on_activate, "toggle")

    def cleanup(self):
        if self._dbus_owner_id:
            Gio.bus_unown_name(self._dbus_owner_id)
