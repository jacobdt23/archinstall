"""Adw.Application setup, CSS styling, CLI flags, and keyboard shortcuts for Orbit Files."""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from orbit_files import APP_ID
from orbit_files.window import MainWindow


class OrbitFilesApp(Adw.Application):
    """Main Libadwaita application class."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.add_main_option(
            "new-window",
            ord("n"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Open a new Orbit Files window",
            None,
        )
        self.add_main_option(
            "place",
            ord("p"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING,
            "Open a named place (home, desktop, documents, downloads, music, pictures, videos, trash, root)",
            "PLACE",
        )

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        self._load_css()
        self._register_shortcuts()

    def _create_window(self, initial_dir: Gio.File | None = None) -> MainWindow:
        win = MainWindow(self, initial_dir=initial_dir)
        win.present()
        return win

    def do_activate(self) -> None:
        win = self.get_active_window()
        if win is None:
            self._create_window()
        else:
            win.present()

    @staticmethod
    def _resolve_place(place: str) -> Gio.File:
        key = place.strip().lower()
        if key == "trash":
            return Gio.File.new_for_uri("trash:///")
        if key in ("root", "filesystem", "/"):
            return Gio.File.new_for_path("/")
        xdg_map = {
            "desktop": GLib.UserDirectory.DIRECTORY_DESKTOP,
            "documents": GLib.UserDirectory.DIRECTORY_DOCUMENTS,
            "downloads": GLib.UserDirectory.DIRECTORY_DOWNLOAD,
            "music": GLib.UserDirectory.DIRECTORY_MUSIC,
            "pictures": GLib.UserDirectory.DIRECTORY_PICTURES,
            "videos": GLib.UserDirectory.DIRECTORY_VIDEOS,
        }
        if key in xdg_map:
            path_str = GLib.get_user_special_dir(xdg_map[key])
            if path_str and Path(path_str).is_dir():
                return Gio.File.new_for_path(path_str)
        return Gio.File.new_for_path(str(Path.home()))

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        options = command_line.get_options_dict().end().unpack()
        new_window = bool(options.get("new-window", False))
        place = options.get("place")
        args = command_line.get_arguments()[1:]

        targets: list[Gio.File] = []
        if isinstance(place, str) and place.strip():
            targets.append(self._resolve_place(place))

        for raw in args:
            if not raw or raw.startswith("-"):
                continue
            if "://" in raw:
                targets.append(Gio.File.new_for_uri(raw))
            else:
                path = Path(raw).expanduser()
                if not path.is_absolute():
                    cwd = command_line.get_cwd()
                    if cwd:
                        path = Path(cwd) / path
                targets.append(Gio.File.new_for_path(str(path)))

        active = self.get_active_window()
        if new_window or active is None or not isinstance(active, MainWindow):
            first = targets[0] if targets else None
            win = self._create_window(initial_dir=first)
            for extra in targets[1:]:
                win.add_tab(extra)
        else:
            if targets:
                for target in targets:
                    active.add_tab(target)
            active.present()

        return 0

    def _load_css(self) -> None:
        css_path = Path(__file__).with_name("style.css")
        if not css_path.exists():
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(str(css_path))
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER,
            )

    def _register_shortcuts(self) -> None:
        shortcuts = {
            "win.new-tab": ["<Control>t"],
            "win.close-tab": ["<Control>w"],
            "win.toggle-split": ["F3"],
            "win.switch-pane": ["F6"],
            "win.toggle-preview": ["F4", "<Control>i"],
            "win.toggle-sidebar": ["F9"],
            "win.toggle-hidden": ["<Control>h"],
            "win.toggle-search": ["<Control>f"],
            "win.focus-location": ["<Control>l"],
            "win.view-list": ["<Control>1"],
            "win.view-grid": ["<Control>2"],
            "win.go-back": ["<Alt>Left"],
            "win.go-forward": ["<Alt>Right"],
            "win.go-up": ["<Alt>Up", "BackSpace"],
            "win.refresh": ["F5", "<Control>r"],
            "win.select-all": ["<Control>a"],
            "win.cut": ["<Control>x"],
            "win.copy": ["<Control>c"],
            "win.paste": ["<Control>v"],
            "win.rename": ["F2"],
            "win.trash": ["Delete"],
            "win.delete-permanent": ["<Shift>Delete"],
            "win.new-folder": ["<Control><Shift>n"],
            "win.properties": ["<Alt>Return"],
            "win.bookmark-current": ["<Control>d"],
        }
        for action_name, accels in shortcuts.items():
            self.set_accels_for_action(action_name, accels)
