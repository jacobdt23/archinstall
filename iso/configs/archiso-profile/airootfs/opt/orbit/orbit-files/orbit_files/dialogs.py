"""Libadwaita dialogs for Orbit Files (Rename, New Folder/File, Delete, Properties)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gi.repository import Adw, Gio, GLib, Gtk

from orbit_files.file_ops import get_folder_stats
from orbit_files.models import FileItem, format_mode, format_size


def prompt_text_dialog(
    parent: Gtk.Window,
    heading: str,
    body: str,
    initial_text: str,
    confirm_label: str,
    on_confirm: Callable[[str], None],
    select_stem: bool = False,
) -> None:
    """Present a clean Libadwaita text prompt dialog."""
    dialog = Adw.AlertDialog.new(heading, body)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("confirm", confirm_label)
    dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("confirm")
    dialog.set_close_response("cancel")

    entry = Gtk.Entry()
    entry.set_text(initial_text)
    entry.set_activates_default(True)
    entry.set_margin_top(6)
    dialog.set_extra_child(entry)

    def _on_response(_dlg: Adw.AlertDialog, response: str) -> None:
        if response == "confirm":
            on_confirm(entry.get_text())

    dialog.connect("response", _on_response)
    dialog.present(parent)

    def _focus_entry() -> bool:
        entry.grab_focus()
        if select_stem and "." in initial_text and not initial_text.startswith("."):
            stem_end = initial_text.rfind(".")
            entry.select_region(0, stem_end)
        else:
            entry.select_region(0, -1)
        return False

    GLib.idle_add(_focus_entry)


def confirm_delete_dialog(
    parent: Gtk.Window,
    items: list[FileItem],
    on_confirm: Callable[[], None],
) -> None:
    """Ask for confirmation before permanently deleting files."""
    if not items:
        return
    if len(items) == 1:
        heading = f"Permanently delete “{items[0].name}”?"
        body = "This item will be permanently deleted and cannot be recovered from Trash."
    else:
        heading = f"Permanently delete {len(items)} items?"
        body = "These items will be permanently deleted and cannot be recovered from Trash."

    dialog = Adw.AlertDialog.new(heading, body)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete Permanently")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def _on_response(_dlg: Adw.AlertDialog, response: str) -> None:
        if response == "delete":
            on_confirm()

    dialog.connect("response", _on_response)
    dialog.present(parent)


def show_properties_dialog(parent: Gtk.Window, item: FileItem) -> None:
    """Display file or folder properties in a Libadwaita dialog."""
    dialog = Adw.Dialog()
    dialog.set_title("Properties")
    dialog.set_content_width(420)
    dialog.set_content_height(460)

    toolbar_view = Adw.ToolbarView()
    header = Adw.HeaderBar()
    toolbar_view.add_top_bar(header)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

    clamp = Adw.Clamp()
    clamp.set_maximum_size(400)
    clamp.set_margin_top(16)
    clamp.set_margin_bottom(24)
    clamp.set_margin_start(16)
    clamp.set_margin_end(16)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

    # Top header with icon + name
    hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    hero.set_halign(Gtk.Align.CENTER)
    icon = Gtk.Image.new_from_gicon(item.gicon)
    icon.set_pixel_size(64)
    hero.append(icon)

    title_label = Gtk.Label(label=item.name)
    title_label.add_css_class("title-2")
    title_label.set_wrap(True)
    title_label.set_justify(Gtk.Justification.CENTER)
    title_label.set_selectable(True)
    hero.append(title_label)
    box.append(hero)

    # Details group
    group = Adw.PreferencesGroup()

    def _add_row(title: str, subtitle: str) -> None:
        if not subtitle:
            return
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(subtitle)
        row.set_subtitle_selectable(True)
        group.add(row)

    _add_row("Type", f"{item.type_display} ({item.content_type})" if item.content_type else item.type_display)

    if item.is_dir and item.path:
        count, total, truncated = get_folder_stats(Path(item.path))
        suffix = "+" if truncated else ""
        noun = "item" if count == 1 else "items"
        _add_row("Contents", f"{count}{suffix} {noun} ({format_size(total)} direct)")
    else:
        _add_row("Size", f"{format_size(item.size)} ({item.size:,} bytes)")

    parent_gfile = item.gfile.get_parent()
    location = (
        parent_gfile.get_path() or parent_gfile.get_uri()
        if parent_gfile is not None
        else item.uri
    )
    _add_row("Location", location)

    if item.trash_orig_path:
        _add_row("Original Location", item.trash_orig_path)
    if item.symlink_target:
        _add_row("Link Target", item.symlink_target)
    if item.mtime_display:
        _add_row("Modified", item.mtime_display)
    if item.unix_mode:
        _add_row("Permissions", format_mode(item.unix_mode))

    box.append(group)
    clamp.set_child(box)
    scrolled.set_child(clamp)
    toolbar_view.set_content(scrolled)
    dialog.set_child(toolbar_view)
    dialog.present(parent)
