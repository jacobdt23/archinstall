"""Collapsible file preview and inspector pane."""

from __future__ import annotations

import threading
from pathlib import Path

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from orbit_files.file_ops import get_folder_stats
from orbit_files.models import FileItem, format_mode, format_size


MAX_TEXT_PREVIEW_BYTES = 4096
MAX_IMAGE_PREVIEW_DIM = 240


class PreviewPane(Gtk.ScrolledWindow):
    """Displays an image/text preview and metadata for the selected file(s)."""

    def __init__(self) -> None:
        super().__init__()
        self._generation = 0

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_size_request(260, -1)
        self.add_css_class("orbit-preview")

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._box.set_margin_top(16)
        self._box.set_margin_bottom(16)
        self._box.set_margin_start(14)
        self._box.set_margin_end(14)

        # Media preview area (stack: icon | picture | text)
        self._media_stack = Gtk.Stack()
        self._media_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._media_stack.set_transition_duration(100)

        self._icon_image = Gtk.Image.new_from_icon_name("folder-symbolic")
        self._icon_image.set_pixel_size(72)
        self._icon_image.set_halign(Gtk.Align.CENTER)
        self._icon_image.set_margin_top(12)
        self._icon_image.set_margin_bottom(8)
        self._media_stack.add_named(self._icon_image, "icon")

        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_size_request(220, 180)
        self._picture.add_css_class("preview-image")
        self._media_stack.add_named(self._picture, "image")

        text_frame = Gtk.Frame()
        text_frame.add_css_class("preview-text-frame")
        self._text_view = Gtk.TextView()
        self._text_view.set_editable(False)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_monospace(True)
        self._text_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        self._text_view.set_top_margin(8)
        self._text_view.set_bottom_margin(8)
        self._text_view.set_left_margin(8)
        self._text_view.set_right_margin(8)
        self._text_view.add_css_class("preview-text")
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_min_content_height(180)
        text_scroll.set_max_content_height(260)
        text_scroll.set_child(self._text_view)
        text_frame.set_child(text_scroll)
        self._media_stack.add_named(text_frame, "text")

        self._box.append(self._media_stack)

        # Title
        self._title_label = Gtk.Label(label="No Selection")
        self._title_label.add_css_class("title-4")
        self._title_label.set_wrap(True)
        self._title_label.set_justify(Gtk.Justification.CENTER)
        self._title_label.set_selectable(True)
        self._box.append(self._title_label)

        self._subtitle_label = Gtk.Label(label="Select a file or folder to inspect")
        self._subtitle_label.add_css_class("dim-label")
        self._subtitle_label.add_css_class("caption")
        self._subtitle_label.set_wrap(True)
        self._subtitle_label.set_justify(Gtk.Justification.CENTER)
        self._box.append(self._subtitle_label)

        self._sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._box.append(self._sep)

        # Metadata key-value grid
        self._meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._box.append(self._meta_box)

        self.set_child(self._box)
        self.show_items([])

    def _clear_meta(self) -> None:
        while (child := self._meta_box.get_first_child()) is not None:
            self._meta_box.remove(child)

    def _add_meta(self, label: str, value: str) -> None:
        if not value:
            return
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        key_lbl = Gtk.Label(label=label)
        key_lbl.set_xalign(0.0)
        key_lbl.add_css_class("dim-label")
        key_lbl.add_css_class("caption")
        row.append(key_lbl)

        val_lbl = Gtk.Label(label=value)
        val_lbl.set_xalign(0.0)
        val_lbl.set_wrap(True)
        val_lbl.set_selectable(True)
        row.append(val_lbl)
        self._meta_box.append(row)

    def show_items(self, items: list[FileItem]) -> None:
        """Update the preview pane for the given selection."""
        self._generation += 1
        gen = self._generation
        self._clear_meta()

        if not items:
            self._icon_image.set_from_icon_name("document-properties-symbolic")
            self._media_stack.set_visible_child_name("icon")
            self._title_label.set_text("No Selection")
            self._subtitle_label.set_text("Select an item to preview")
            self._sep.set_visible(False)
            return

        self._sep.set_visible(True)

        if len(items) > 1:
            self._icon_image.set_from_icon_name("edit-select-all-symbolic")
            self._media_stack.set_visible_child_name("icon")
            self._title_label.set_text(f"{len(items)} items selected")
            dirs = sum(1 for i in items if i.is_dir)
            files = len(items) - dirs
            total_size = sum(i.size for i in items if not i.is_dir)
            parts = []
            if dirs:
                parts.append(f"{dirs} folder{'s' if dirs != 1 else ''}")
            if files:
                parts.append(f"{files} file{'s' if files != 1 else ''}")
            self._subtitle_label.set_text(", ".join(parts))
            if files:
                self._add_meta("Total File Size", format_size(total_size))
            return

        item = items[0]
        self._title_label.set_text(item.name)
        self._subtitle_label.set_text(item.type_display)
        self._icon_image.set_from_gicon(item.gicon)
        self._media_stack.set_visible_child_name("icon")

        if not item.is_dir:
            self._add_meta("Size", f"{format_size(item.size)} ({item.size:,} B)")
        if item.mtime_display:
            self._add_meta("Modified", item.mtime_display)
        if item.unix_mode:
            self._add_meta("Permissions", format_mode(item.unix_mode))
        if item.symlink_target:
            self._add_meta("Link Target", item.symlink_target)
        if item.path:
            self._add_meta("Path", item.path)

        if not item.path:
            return

        path = Path(item.path)
        if item.is_dir:
            self._load_folder_summary_async(path, gen)
        elif item.is_image:
            self._load_image_async(path, gen)
        elif item.is_text and item.size <= 5 * 1024 * 1024:
            self._load_text_async(path, gen)

    def _load_folder_summary_async(self, path: Path, gen: int) -> None:
        def _worker() -> None:
            count, total, truncated = get_folder_stats(path)
            GLib.idle_add(self._apply_folder_summary, gen, count, total, truncated)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_folder_summary(
        self, gen: int, count: int, total: int, truncated: bool
    ) -> bool:
        if gen != self._generation:
            return False
        suffix = "+" if truncated else ""
        noun = "item" if count == 1 else "items"
        self._add_meta("Contents", f"{count}{suffix} {noun} ({format_size(total)} direct)")
        return False

    def _load_image_async(self, path: Path, gen: int) -> None:
        def _worker() -> None:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(path),
                    MAX_IMAGE_PREVIEW_DIM,
                    MAX_IMAGE_PREVIEW_DIM,
                    True,
                )
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                GLib.idle_add(self._apply_image, gen, texture)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_image(self, gen: int, texture: Gdk.Texture) -> bool:
        if gen != self._generation:
            return False
        self._picture.set_paintable(texture)
        self._media_stack.set_visible_child_name("image")
        return False

    def _load_text_async(self, path: Path, gen: int) -> None:
        def _worker() -> None:
            try:
                with path.open("rb") as fh:
                    raw = fh.read(MAX_TEXT_PREVIEW_BYTES)
                if b"\x00" in raw:
                    return
                text = raw.decode("utf-8", errors="replace")
                if len(raw) == MAX_TEXT_PREVIEW_BYTES:
                    text += "\n…"
                GLib.idle_add(self._apply_text, gen, text)
            except OSError:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_text(self, gen: int, text: str) -> bool:
        if gen != self._generation:
            return False
        buf = self._text_view.get_buffer()
        buf.set_text(text)
        self._media_stack.set_visible_child_name("text")
        return False
