"""Orbit View — A fast GTK 4 + Libadwaita image viewer in Python."""

from __future__ import annotations

import sys
from pathlib import Path

from orbit_suite import __version__
from orbit_suite.common import load_css_string

from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, Gtk

APP_ID = "dev.orbit.View"
APP_NAME = "Orbit View"

IMAGE_EXTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
    ".svg", ".tif", ".tiff", ".avif", ".ico", ".jxl",
}

VIEW_CSS = """
.orbit-view-canvas {
    background-color: #111318;
}
.orbit-view-info {
    background-color: alpha(@window_fg_color, 0.03);
}
.orbit-view-statusbar {
    border-top: 1px solid alpha(@borders, 0.6);
}
"""


def _format_size(size: int) -> str:
    val = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if val < 1024.0 or unit == "GB":
            return f"{int(val)} B" if unit == "B" else f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{size} B"


class OrbitViewWindow(Adw.ApplicationWindow):
    """Main Orbit View image viewer window."""

    def __init__(self, app: Adw.Application, initial_file: Path | None = None) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(980, 680)

        self._gallery: list[Path] = []
        self._index: int = -1
        self._base_pixbuf: GdkPixbuf.Pixbuf | None = None
        self._rotation: int = 0
        self._zoom: float = 1.0
        self._fit_mode: bool = True
        self._slideshow_id: int | None = None

        self._setup_actions()
        self._build_ui()

        if initial_file is not None and initial_file.exists():
            self.load_path(initial_file)

    def _build_ui(self) -> None:
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        toolbar_view = Adw.ToolbarView()
        self._toast_overlay.set_child(toolbar_view)

        header = Adw.HeaderBar()

        open_btn = Gtk.Button.new_from_icon_name("document-open-symbolic")
        open_btn.set_tooltip_text("Open Image (Ctrl+O)")
        open_btn.set_action_name("win.open")
        header.pack_start(open_btn)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.add_css_class("linked")
        self._prev_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._prev_btn.set_tooltip_text("Previous Image (Left)")
        self._prev_btn.set_action_name("win.prev")
        nav_box.append(self._prev_btn)

        self._next_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self._next_btn.set_tooltip_text("Next Image (Right)")
        self._next_btn.set_action_name("win.next")
        nav_box.append(self._next_btn)
        header.pack_start(nav_box)

        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_box.add_css_class("linked")
        for icon, tip, act in (
            ("zoom-out-symbolic", "Zoom Out (-)", "win.zoom-out"),
            ("zoom-fit-best-symbolic", "Fit to Window (0)", "win.zoom-fit"),
            ("zoom-original-symbolic", "Actual Size (1)", "win.zoom-100"),
            ("zoom-in-symbolic", "Zoom In (+)", "win.zoom-in"),
        ):
            btn = Gtk.Button.new_from_icon_name(icon)
            btn.set_tooltip_text(tip)
            btn.set_action_name(act)
            zoom_box.append(btn)
        header.set_title_widget(zoom_box)

        self._info_btn = Gtk.ToggleButton()
        self._info_btn.set_icon_name("dialog-information-symbolic")
        self._info_btn.set_tooltip_text("Toggle Image Info (I)")
        self._info_btn.connect(
            "toggled", lambda b: self._info_revealer.set_reveal_child(b.get_active())
        )
        header.pack_end(self._info_btn)

        rot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        rot_box.add_css_class("linked")
        rot_l = Gtk.Button.new_from_icon_name("object-rotate-left-symbolic")
        rot_l.set_tooltip_text("Rotate Left ([)")
        rot_l.set_action_name("win.rotate-left")
        rot_box.append(rot_l)
        rot_r = Gtk.Button.new_from_icon_name("object-rotate-right-symbolic")
        rot_r.set_tooltip_text("Rotate Right (])")
        rot_r.set_action_name("win.rotate-right")
        rot_box.append(rot_r)
        header.pack_end(rot_box)

        self._slide_btn = Gtk.ToggleButton()
        self._slide_btn.set_icon_name("media-playback-start-symbolic")
        self._slide_btn.set_tooltip_text("Slideshow (Space)")
        self._slide_btn.connect("toggled", self._on_slideshow_toggled)
        header.pack_end(self._slide_btn)

        toolbar_view.add_top_bar(header)

        # Main canvas + info drawer
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body.set_hexpand(True)
        body.set_vexpand(True)

        self._stack = Gtk.Stack()
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)

        empty = Adw.StatusPage()
        empty.set_icon_name("image-x-generic-symbolic")
        empty.set_title("Orbit View")
        empty.set_description("Open an image or drag one into this window.")
        open_empty = Gtk.Button.new_with_label("Open Image…")
        open_empty.add_css_class("suggested-action")
        open_empty.add_css_class("pill")
        open_empty.set_halign(Gtk.Align.CENTER)
        open_empty.set_action_name("win.open")
        empty.set_child(open_empty)
        self._stack.add_named(empty, "empty")

        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.add_css_class("orbit-view-canvas")
        self._scrolled.set_hexpand(True)
        self._scrolled.set_vexpand(True)

        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_halign(Gtk.Align.CENTER)
        self._picture.set_valign(Gtk.Align.CENTER)
        self._scrolled.set_child(self._picture)
        self._stack.add_named(self._scrolled, "image")
        self._stack.set_visible_child_name("empty")

        body.append(self._stack)

        # Collapsible metadata panel
        self._info_revealer = Gtk.Revealer()
        self._info_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self._info_revealer.set_reveal_child(False)
        info_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        info_wrap.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self._info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._info_box.add_css_class("orbit-view-info")
        self._info_box.set_size_request(240, -1)
        self._info_box.set_margin_top(16)
        self._info_box.set_margin_bottom(16)
        self._info_box.set_margin_start(14)
        self._info_box.set_margin_end(14)
        info_wrap.append(self._info_box)
        self._info_revealer.set_child(info_wrap)
        body.append(self._info_revealer)

        toolbar_view.set_content(body)

        # Status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.add_css_class("orbit-view-statusbar")
        status_bar.set_margin_top(4)
        status_bar.set_margin_bottom(4)
        status_bar.set_margin_start(12)
        status_bar.set_margin_end(12)

        self._status_left = Gtk.Label(label="No image loaded")
        self._status_left.set_xalign(0.0)
        self._status_left.set_hexpand(True)
        self._status_left.add_css_class("caption")
        self._status_left.add_css_class("dim-label")
        status_bar.append(self._status_left)

        self._status_right = Gtk.Label(label="")
        self._status_right.set_xalign(1.0)
        self._status_right.add_css_class("caption")
        self._status_right.add_css_class("dim-label")
        status_bar.append(self._status_right)
        toolbar_view.add_bottom_bar(status_bar)

        # Drag-and-drop image files onto window
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)

        def _on_drop(_dt: Gtk.DropTarget, value: object, _x: float, _y: float) -> bool:
            if isinstance(value, Gdk.FileList):
                files = list(value.get_files())
                if files and files[0].get_path():
                    self.load_path(Path(files[0].get_path()))
                    return True
            return False

        drop_target.connect("drop", _on_drop)
        self.add_controller(drop_target)

    def _setup_actions(self) -> None:
        actions = [
            ("open", self._act_open),
            ("prev", lambda *_: self._step(-1)),
            ("next", lambda *_: self._step(1)),
            ("zoom-in", lambda *_: self._set_zoom(self._zoom * 1.25)),
            ("zoom-out", lambda *_: self._set_zoom(self._zoom / 1.25)),
            ("zoom-100", lambda *_: self._set_zoom(1.0)),
            ("zoom-fit", lambda *_: self._set_fit()),
            ("rotate-left", lambda *_: self._rotate(-90)),
            ("rotate-right", lambda *_: self._rotate(90)),
            ("toggle-info", lambda *_: self._info_btn.set_active(not self._info_btn.get_active())),
            ("toggle-slideshow", lambda *_: self._slide_btn.set_active(not self._slide_btn.get_active())),
            ("toggle-fullscreen", self._act_fullscreen),
        ]
        for name, cb in actions:
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", cb)
            self.add_action(act)

    def load_path(self, path: Path) -> None:
        if path.is_dir():
            imgs = sorted(
                (p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
                key=lambda p: p.name.casefold(),
            )
            if not imgs:
                self._toast_overlay.add_toast(Adw.Toast.new("No images found in folder"))
                return
            self._gallery = imgs
            self._index = 0
        else:
            parent = path.parent
            imgs = sorted(
                (p for p in parent.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
                key=lambda p: p.name.casefold(),
            )
            self._gallery = imgs if path in imgs else [path]
            self._index = self._gallery.index(path)

        self._load_current()

    def _load_current(self) -> None:
        if not (0 <= self._index < len(self._gallery)):
            return
        path = self._gallery[self._index]
        try:
            self._base_pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(path))
        except GLib.Error as err:
            self._toast_overlay.add_toast(Adw.Toast.new(f"Cannot load image: {err.message}"))
            return

        self._rotation = 0
        self._fit_mode = True
        self._zoom = 1.0
        self._render_current()
        self._stack.set_visible_child_name("image")
        self._update_metadata(path)
        self._prev_btn.set_sensitive(len(self._gallery) > 1)
        self._next_btn.set_sensitive(len(self._gallery) > 1)

    def _render_current(self) -> None:
        if self._base_pixbuf is None:
            return
        pb = self._base_pixbuf
        rot_map = {
            90: GdkPixbuf.PixbufRotation.CLOCKWISE,
            180: GdkPixbuf.PixbufRotation.UPSIDEDOWN,
            270: GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE,
        }
        if self._rotation in rot_map:
            pb = pb.rotate_simple(rot_map[self._rotation])

        texture = Gdk.Texture.new_for_pixbuf(pb)
        self._picture.set_paintable(texture)

        if self._fit_mode:
            self._picture.set_can_shrink(True)
            self._picture.set_size_request(-1, -1)
            zoom_label = "Fit"
        else:
            self._picture.set_can_shrink(False)
            w = max(16, int(pb.get_width() * self._zoom))
            h = max(16, int(pb.get_height() * self._zoom))
            self._picture.set_size_request(w, h)
            zoom_label = f"{int(self._zoom * 100)}%"

        path = self._gallery[self._index]
        self.set_title(f"{path.name} — {APP_NAME}")
        self._status_left.set_text(
            f"{path.name}  ({self._index + 1} / {len(self._gallery)})"
        )
        self._status_right.set_text(
            f"{pb.get_width()} × {pb.get_height()} px  •  {zoom_label}"
        )

    def _update_metadata(self, path: Path) -> None:
        while (child := self._info_box.get_first_child()) is not None:
            self._info_box.remove(child)

        heading = Gtk.Label(label="Image Info")
        heading.set_xalign(0.0)
        heading.add_css_class("title-4")
        self._info_box.append(heading)

        def _add(k: str, v: str) -> None:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            kl = Gtk.Label(label=k)
            kl.set_xalign(0.0)
            kl.add_css_class("caption")
            kl.add_css_class("dim-label")
            row.append(kl)
            vl = Gtk.Label(label=v)
            vl.set_xalign(0.0)
            vl.set_wrap(True)
            vl.set_selectable(True)
            row.append(vl)
            self._info_box.append(row)

        _add("Filename", path.name)
        if self._base_pixbuf is not None:
            _add("Dimensions", f"{self._base_pixbuf.get_width()} × {self._base_pixbuf.get_height()} px")
        try:
            _add("File Size", _format_size(path.stat().st_size))
        except OSError:
            pass
        _add("Format", path.suffix.lstrip(".").upper() or "Image")
        _add("Folder", str(path.parent))

    def _step(self, delta: int) -> None:
        if len(self._gallery) <= 1:
            return
        self._index = (self._index + delta) % len(self._gallery)
        self._load_current()

    def _set_zoom(self, factor: float) -> None:
        if self._base_pixbuf is None:
            return
        self._fit_mode = False
        self._zoom = max(0.1, min(8.0, factor))
        self._render_current()

    def _set_fit(self) -> None:
        if self._base_pixbuf is None:
            return
        self._fit_mode = True
        self._zoom = 1.0
        self._render_current()

    def _rotate(self, delta: int) -> None:
        if self._base_pixbuf is None:
            return
        self._rotation = (self._rotation + delta) % 360
        self._render_current()

    def _on_slideshow_toggled(self, btn: Gtk.ToggleButton) -> None:
        if self._slideshow_id is not None:
            GLib.source_remove(self._slideshow_id)
            self._slideshow_id = None
        if btn.get_active() and len(self._gallery) > 1:
            btn.set_icon_name("media-playback-pause-symbolic")
            self._slideshow_id = GLib.timeout_add_seconds(3, self._advance_slideshow)
        else:
            btn.set_icon_name("media-playback-start-symbolic")

    def _advance_slideshow(self) -> bool:
        self._step(1)
        return True

    def _act_fullscreen(self, *_args: object) -> None:
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

    def _act_open(self, *_args: object) -> None:
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Open Image")
        flt = Gtk.FileFilter()
        flt.set_name("Images")
        flt.add_mime_type("image/*")
        store = Gio.ListStore.new(Gtk.FileFilter)
        store.append(flt)
        dialog.set_filters(store)

        def _done(dlg: Gtk.FileDialog, res: Gio.AsyncResult) -> None:
            try:
                gfile = dlg.open_finish(res)
                if gfile and gfile.get_path():
                    self.load_path(Path(gfile.get_path()))
            except GLib.Error:
                pass

        dialog.open(self, None, _done)


class OrbitViewApp(Adw.Application):
    """Orbit View application."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        load_css_string(VIEW_CSS)
        shortcuts = {
            "win.open": ["<Control>o"],
            "win.prev": ["Left", "BackSpace"],
            "win.next": ["Right"],
            "win.zoom-in": ["plus", "equal", "<Control>plus", "<Control>equal"],
            "win.zoom-out": ["minus", "<Control>minus"],
            "win.zoom-fit": ["0", "f"],
            "win.zoom-100": ["1"],
            "win.rotate-left": ["bracketleft"],
            "win.rotate-right": ["bracketright"],
            "win.toggle-info": ["i"],
            "win.toggle-slideshow": ["space"],
            "win.toggle-fullscreen": ["F11"],
        }
        for name, accels in shortcuts.items():
            self.set_accels_for_action(name, accels)

    def do_activate(self) -> None:
        win = self.get_active_window()
        if win is None:
            win = OrbitViewWindow(self)
        win.present()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        args = [a for a in command_line.get_arguments()[1:] if a and not a.startswith("-")]
        target: Path | None = None
        if args:
            raw = args[0]
            if raw.startswith("file://"):
                gfile = Gio.File.new_for_uri(raw)
                if gfile.get_path():
                    target = Path(gfile.get_path())
            else:
                p = Path(raw).expanduser()
                if not p.is_absolute() and command_line.get_cwd():
                    p = Path(command_line.get_cwd()) / p
                target = p
        win = OrbitViewWindow(self, initial_file=target)
        win.present()
        return 0


def main(argv: list[str] | None = None) -> int:
    app = OrbitViewApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
