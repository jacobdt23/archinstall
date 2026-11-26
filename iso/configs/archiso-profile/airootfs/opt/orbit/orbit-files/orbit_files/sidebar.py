"""Sidebar widget with Places, Bookmarks, and Mounted Drives."""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Callable

from gi.repository import Gdk, Gio, GLib, GObject, Gtk


BOOKMARKS_FILE = Path.home() / ".config" / "gtk-3.0" / "bookmarks"


class SidebarRow(Gtk.ListBoxRow):
    """A single navigable row in the sidebar."""

    def __init__(
        self,
        label: str,
        icon: Gio.Icon | str,
        target: Gio.File,
        on_drop_files: Callable[[list[Gio.File], Gio.File, bool], None] | None = None,
        extra_widget: Gtk.Widget | None = None,
    ) -> None:
        super().__init__()
        self.target = target
        self.add_css_class("sidebar-item")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(10)
        box.set_margin_end(8)

        if isinstance(icon, str):
            img = Gtk.Image.new_from_icon_name(icon)
        else:
            img = Gtk.Image.new_from_gicon(icon)
        img.set_pixel_size(16)
        box.append(img)

        lbl = Gtk.Label(label=label)
        lbl.set_xalign(0.0)
        lbl.set_hexpand(True)
        lbl.set_ellipsize(3)  # END
        box.append(lbl)

        if extra_widget is not None:
            box.append(extra_widget)

        self.set_child(box)

        # Allow dropping files onto any local folder row in the sidebar
        if on_drop_files is not None and target.get_path():
            drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.MOVE | Gdk.DragAction.COPY)

            def _on_drop(
                _dt: Gtk.DropTarget,
                value: object,
                _x: float,
                _y: float,
            ) -> bool:
                if isinstance(value, Gdk.FileList):
                    files = list(value.get_files())
                    if files:
                        on_drop_files(files, self.target, False)
                        return True
                return False

            drop_target.connect("drop", _on_drop)
            self.add_controller(drop_target)


class PlacesSidebar(Gtk.ScrolledWindow):
    """COSMIC / Thunar style sidebar with Places, Bookmarks, and Mounted Drives."""

    def __init__(
        self,
        on_navigate: Callable[[Gio.File], None],
        on_drop_files: Callable[[list[Gio.File], Gio.File, bool], None] | None = None,
        on_notify: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__()
        self._on_navigate = on_navigate
        self._on_drop_files = on_drop_files
        self._on_notify = on_notify
        self._suppress_select = False

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_size_request(210, -1)
        self.add_css_class("orbit-sidebar")

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        container.set_margin_top(8)
        container.set_margin_bottom(12)
        container.set_margin_start(6)
        container.set_margin_end(6)

        # Places section
        container.append(self._make_section_header("Places"))
        self._places_list = self._make_listbox()
        container.append(self._places_list)

        # Bookmarks section
        self._bookmarks_header = self._make_section_header("Bookmarks")
        container.append(self._bookmarks_header)
        self._bookmarks_list = self._make_listbox()
        container.append(self._bookmarks_list)

        # Devices / Mounts section
        self._mounts_header = self._make_section_header("Devices")
        container.append(self._mounts_header)
        self._mounts_list = self._make_listbox()
        container.append(self._mounts_list)

        self.set_child(container)

        self._populate_places()
        self.refresh_bookmarks()

        self._volume_monitor = Gio.VolumeMonitor.get()
        self._volume_monitor.connect("mount-added", lambda *_: self.refresh_mounts())
        self._volume_monitor.connect("mount-removed", lambda *_: self.refresh_mounts())
        self._volume_monitor.connect("mount-changed", lambda *_: self.refresh_mounts())
        self.refresh_mounts()

    def _make_section_header(self, title: str) -> Gtk.Label:
        lbl = Gtk.Label(label=title)
        lbl.set_xalign(0.0)
        lbl.add_css_class("heading")
        lbl.add_css_class("dim-label")
        lbl.add_css_class("sidebar-section-label")
        lbl.set_margin_start(10)
        lbl.set_margin_top(4)
        return lbl

    def _make_listbox(self) -> Gtk.ListBox:
        lb = Gtk.ListBox()
        lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        lb.add_css_class("navigation-sidebar")
        lb.connect("row-activated", self._on_row_activated)
        return lb

    def _clear_listbox(self, lb: Gtk.ListBox) -> None:
        while (row := lb.get_first_child()) is not None:
            lb.remove(row)

    def _on_row_activated(self, active_list: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if self._suppress_select or not isinstance(row, SidebarRow):
            return
        # Clear selection in other lists for a unified sidebar feel
        for lb in (self._places_list, self._bookmarks_list, self._mounts_list):
            if lb is not active_list:
                lb.unselect_all()
        self._on_navigate(row.target)

    def highlight_location(self, gfile: Gio.File) -> None:
        """Select the sidebar row matching gfile, if any."""
        target_uri = gfile.get_uri().rstrip("/")
        self._suppress_select = True
        try:
            for lb in (self._places_list, self._bookmarks_list, self._mounts_list):
                lb.unselect_all()
                child = lb.get_first_child()
                while child is not None:
                    if isinstance(child, SidebarRow):
                        if child.target.get_uri().rstrip("/") == target_uri:
                            lb.select_row(child)
                            break
                    child = child.get_next_sibling()
        finally:
            self._suppress_select = False

    def _populate_places(self) -> None:
        self._clear_listbox(self._places_list)

        places: list[tuple[str, str, Gio.File]] = [
            ("Home", "user-home-symbolic", Gio.File.new_for_path(str(Path.home()))),
        ]

        xdg_specs = [
            (GLib.UserDirectory.DIRECTORY_DESKTOP, "Desktop", "user-desktop-symbolic"),
            (GLib.UserDirectory.DIRECTORY_DOCUMENTS, "Documents", "folder-documents-symbolic"),
            (GLib.UserDirectory.DIRECTORY_DOWNLOAD, "Downloads", "folder-download-symbolic"),
            (GLib.UserDirectory.DIRECTORY_MUSIC, "Music", "folder-music-symbolic"),
            (GLib.UserDirectory.DIRECTORY_PICTURES, "Pictures", "folder-pictures-symbolic"),
            (GLib.UserDirectory.DIRECTORY_VIDEOS, "Videos", "folder-videos-symbolic"),
        ]
        home_str = str(Path.home())
        for user_dir, label, icon_name in xdg_specs:
            path_str = GLib.get_user_special_dir(user_dir)
            if path_str and path_str != home_str and Path(path_str).is_dir():
                places.append((label, icon_name, Gio.File.new_for_path(path_str)))

        places.append(("Trash", "user-trash-symbolic", Gio.File.new_for_uri("trash:///")))
        places.append(("File System", "drive-harddisk-symbolic", Gio.File.new_for_path("/")))

        for label, icon_name, target in places:
            row = SidebarRow(label, icon_name, target, on_drop_files=self._on_drop_files)
            self._places_list.append(row)

    def _read_bookmarks(self) -> list[tuple[str, str]]:
        """Read GTK bookmarks as (uri, label) pairs."""
        if not BOOKMARKS_FILE.exists():
            return []
        entries: list[tuple[str, str]] = []
        try:
            for line in BOOKMARKS_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1)
                uri = parts[0]
                if len(parts) > 1 and parts[1].strip():
                    label = parts[1].strip()
                else:
                    parsed = urllib.parse.urlparse(uri)
                    label = Path(urllib.parse.unquote(parsed.path)).name or uri
                entries.append((uri, label))
        except OSError:
            pass
        return entries

    def _write_bookmarks(self, entries: list[tuple[str, str]]) -> None:
        BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{uri} {label}" if label else uri for uri, label in entries]
        BOOKMARKS_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def add_bookmark(self, gfile: Gio.File) -> bool:
        """Add gfile to GTK bookmarks. Returns True if added, False if already present."""
        uri = gfile.get_uri()
        entries = self._read_bookmarks()
        if any(u == uri for u, _ in entries):
            return False
        path_str = gfile.get_path()
        label = Path(path_str).name if path_str else (gfile.get_basename() or uri)
        entries.append((uri, label))
        self._write_bookmarks(entries)
        self.refresh_bookmarks()
        return True

    def remove_bookmark(self, uri: str) -> None:
        entries = [(u, lbl) for u, lbl in self._read_bookmarks() if u != uri]
        self._write_bookmarks(entries)
        self.refresh_bookmarks()

    def refresh_bookmarks(self) -> None:
        self._clear_listbox(self._bookmarks_list)
        entries = self._read_bookmarks()
        has_any = bool(entries)
        self._bookmarks_header.set_visible(has_any)
        self._bookmarks_list.set_visible(has_any)

        for uri, label in entries:
            gfile = Gio.File.new_for_uri(uri)
            remove_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
            remove_btn.add_css_class("flat")
            remove_btn.add_css_class("circular")
            remove_btn.add_css_class("sidebar-action-btn")
            remove_btn.set_tooltip_text("Remove Bookmark")
            remove_btn.connect("clicked", lambda _b, u=uri: self.remove_bookmark(u))

            row = SidebarRow(
                label,
                "folder-symbolic",
                gfile,
                on_drop_files=self._on_drop_files,
                extra_widget=remove_btn,
            )
            self._bookmarks_list.append(row)

    def refresh_mounts(self) -> None:
        self._clear_listbox(self._mounts_list)
        mounts = self._volume_monitor.get_mounts()
        visible_mounts = [m for m in mounts if not m.is_shadowed()]

        self._mounts_header.set_visible(bool(visible_mounts))
        self._mounts_list.set_visible(bool(visible_mounts))

        for mount in visible_mounts:
            root = mount.get_root()
            name = mount.get_name() or root.get_basename() or "Drive"
            icon = mount.get_symbolic_icon() or mount.get_icon() or Gio.ThemedIcon.new("drive-removable-media-symbolic")

            eject_btn: Gtk.Widget | None = None
            if mount.can_unmount():
                btn = Gtk.Button.new_from_icon_name("media-eject-symbolic")
                btn.add_css_class("flat")
                btn.add_css_class("circular")
                btn.add_css_class("sidebar-action-btn")
                btn.set_tooltip_text(f"Unmount {name}")
                btn.connect("clicked", lambda _b, m=mount, n=name: self._unmount(m, n))
                eject_btn = btn

            row = SidebarRow(
                name,
                icon,
                root,
                on_drop_files=self._on_drop_files,
                extra_widget=eject_btn,
            )
            self._mounts_list.append(row)

    def _unmount(self, mount: Gio.Mount, name: str) -> None:
        def _done(m: Gio.Mount, res: Gio.AsyncResult) -> None:
            try:
                m.unmount_with_operation_finish(res)
                if self._on_notify:
                    self._on_notify(f"Unmounted {name}")
            except GLib.Error as err:
                if self._on_notify:
                    self._on_notify(f"Could not unmount {name}: {err.message}")

        mount.unmount_with_operation(
            Gio.MountUnmountFlags.NONE,
            None,
            None,
            _done,
        )
