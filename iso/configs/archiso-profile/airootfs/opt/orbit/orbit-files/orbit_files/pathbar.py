"""Breadcrumb path bar with Ctrl+L editable location entry."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gi.repository import Gdk, Gio, GLib, Gtk


class PathBar(Gtk.Box):
    """Displays clickable path breadcrumbs and switches to a path entry on demand."""

    def __init__(self, on_navigate: Callable[[Gio.File], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._on_navigate = on_navigate
        self._current_gfile: Gio.File = Gio.File.new_for_path(str(Path.home()))
        self.set_hexpand(True)
        self.add_css_class("pathbar-container")

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(120)
        self._stack.set_hexpand(True)

        # Breadcrumb view
        crumb_scroll = Gtk.ScrolledWindow()
        crumb_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        crumb_scroll.set_hexpand(True)
        crumb_scroll.set_propagate_natural_height(True)

        self._crumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self._crumb_box.add_css_class("pathbar-crumbs")
        self._crumb_box.set_valign(Gtk.Align.CENTER)
        crumb_scroll.set_child(self._crumb_box)

        # Editable location entry
        self._entry = Gtk.Entry()
        self._entry.set_hexpand(True)
        self._entry.set_placeholder_text("Enter path or URI (e.g. ~/Documents, trash:///)")
        self._entry.connect("activate", self._on_entry_activate)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_entry_key_pressed)
        self._entry.add_controller(key_ctrl)

        focus_ctrl = Gtk.EventControllerFocus()
        focus_ctrl.connect("leave", lambda _ctrl: self.show_breadcrumbs())
        self._entry.add_controller(focus_ctrl)

        self._stack.add_named(crumb_scroll, "crumbs")
        self._stack.add_named(self._entry, "entry")
        self._stack.set_visible_child_name("crumbs")
        self.append(self._stack)

        # Toggle button to edit path directly
        self._edit_btn = Gtk.Button.new_from_icon_name("document-edit-symbolic")
        self._edit_btn.add_css_class("flat")
        self._edit_btn.set_tooltip_text("Edit Location (Ctrl+L)")
        self._edit_btn.connect("clicked", lambda _b: self.focus_entry())
        self.append(self._edit_btn)

    def set_location(self, gfile: Gio.File) -> None:
        self._current_gfile = gfile
        self._rebuild_breadcrumbs(gfile)
        if self._stack.get_visible_child_name() == "entry":
            self._entry.set_text(gfile.get_path() or gfile.get_uri())

    def focus_entry(self) -> None:
        text = self._current_gfile.get_path() or self._current_gfile.get_uri()
        self._entry.set_text(text)
        self._stack.set_visible_child_name("entry")
        self._entry.grab_focus()
        self._entry.select_region(0, -1)

    def show_breadcrumbs(self) -> None:
        self._stack.set_visible_child_name("crumbs")

    def _rebuild_breadcrumbs(self, gfile: Gio.File) -> None:
        while (child := self._crumb_box.get_first_child()) is not None:
            self._crumb_box.remove(child)

        uri = gfile.get_uri()
        path_str = gfile.get_path()

        if uri.startswith("trash:"):
            self._add_crumb("Trash", Gio.File.new_for_uri("trash:///"), is_current=True, icon_name="user-trash-symbolic")
            return

        if not path_str:
            self._add_crumb(uri, gfile, is_current=True)
            return

        path = Path(path_str)
        home = Path.home()

        segments: list[tuple[str, Path, str | None]] = []
        try:
            rel = path.relative_to(home)
            segments.append(("Home", home, "user-home-symbolic"))
            acc = home
            for part in rel.parts:
                acc = acc / part
                segments.append((part, acc, None))
        except ValueError:
            segments.append(("/", Path("/"), "drive-harddisk-symbolic"))
            acc = Path("/")
            for part in path.parts[1:]:
                acc = acc / part
                segments.append((part, acc, None))

        for idx, (label, seg_path, icon_name) in enumerate(segments):
            if idx > 0:
                sep = Gtk.Image.new_from_icon_name("go-next-symbolic")
                sep.add_css_class("dim-label")
                sep.set_pixel_size(12)
                self._crumb_box.append(sep)
            is_last = idx == len(segments) - 1
            self._add_crumb(
                label,
                Gio.File.new_for_path(str(seg_path)),
                is_current=is_last,
                icon_name=icon_name,
            )

    def _add_crumb(
        self,
        label: str,
        target: Gio.File,
        is_current: bool,
        icon_name: str | None = None,
    ) -> None:
        btn = Gtk.Button()
        btn.add_css_class("flat")
        btn.add_css_class("pathbar-crumb")
        if is_current:
            btn.add_css_class("pathbar-crumb-active")

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.set_pixel_size(14)
            content.append(img)
        lbl = Gtk.Label(label=label)
        lbl.set_ellipsize(3)  # Pango.EllipsizeMode.END
        lbl.set_max_width_chars(24)
        content.append(lbl)
        btn.set_child(content)

        btn.connect("clicked", lambda _b, f=target: self._on_navigate(f))
        self._crumb_box.append(btn)

    def _on_entry_activate(self, entry: Gtk.Entry) -> None:
        raw = entry.get_text().strip()
        if not raw:
            self.show_breadcrumbs()
            return
        if "://" in raw:
            target = Gio.File.new_for_uri(raw)
        else:
            expanded = Path(raw).expanduser()
            target = Gio.File.new_for_path(str(expanded))
        self.show_breadcrumbs()
        self._on_navigate(target)

    def _on_entry_key_pressed(
        self,
        _ctrl: Gtk.EventControllerKey,
        keyval: int,
        _keycode: int,
        _state: Gdk.ModifierType,
    ) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.show_breadcrumbs()
            return True
        return False
