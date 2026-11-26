"""Data models and directory loading helpers for Orbit Files."""

from __future__ import annotations

import datetime
import stat
from pathlib import Path

from gi.repository import Gio, GLib, GObject

FILE_QUERY_ATTRS = ",".join(
    [
        Gio.FILE_ATTRIBUTE_STANDARD_NAME,
        Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
        Gio.FILE_ATTRIBUTE_STANDARD_TYPE,
        Gio.FILE_ATTRIBUTE_STANDARD_SIZE,
        Gio.FILE_ATTRIBUTE_STANDARD_ICON,
        Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
        Gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,
        Gio.FILE_ATTRIBUTE_STANDARD_IS_SYMLINK,
        Gio.FILE_ATTRIBUTE_STANDARD_SYMLINK_TARGET,
        Gio.FILE_ATTRIBUTE_TIME_MODIFIED,
        Gio.FILE_ATTRIBUTE_UNIX_MODE,
        Gio.FILE_ATTRIBUTE_TRASH_ORIG_PATH,
    ]
)


def format_size(size: int) -> str:
    """Format a byte count into a human-readable string."""
    if size < 0:
        return ""
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    value = float(size)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{size} B"


def format_mtime(timestamp: int) -> str:
    """Format a Unix timestamp into a readable local date/time string."""
    if timestamp <= 0:
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
    except (OSError, OverflowError, ValueError):
        return ""
    now = datetime.datetime.now()
    if dt.date() == now.date():
        return dt.strftime("Today, %H:%M")
    if dt.year == now.year:
        return dt.strftime("%b %d, %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def format_mode(mode: int) -> str:
    """Format Unix file permissions as e.g. 'rwxr-xr-x (755)'."""
    if mode <= 0:
        return ""
    perm_str = stat.filemode(mode)
    octal = oct(stat.S_IMODE(mode))[2:]
    return f"{perm_str} ({octal})"


class FileItem(GObject.Object):
    """Represents a single file or directory entry in a view."""

    __gtype_name__ = "OrbitFileItem"

    def __init__(self, gfile: Gio.File, info: Gio.FileInfo) -> None:
        super().__init__()
        self.gfile: Gio.File = gfile
        self.uri: str = gfile.get_uri()
        self.path: str | None = gfile.get_path()

        self.name: str = info.get_display_name() or info.get_name() or ""
        self.raw_name: str = info.get_name() or self.name
        self.file_type: Gio.FileType = info.get_file_type()
        self.is_dir: bool = self.file_type == Gio.FileType.DIRECTORY
        self.is_symlink: bool = info.get_is_symlink()
        self.is_hidden: bool = info.get_is_hidden() or self.raw_name.startswith(".")

        self.size: int = 0 if self.is_dir else info.get_size()
        self.size_display: str = "—" if self.is_dir else format_size(self.size)

        dt = info.get_modification_date_time()
        self.mtime: int = int(dt.to_unix()) if dt is not None else 0
        self.mtime_display: str = format_mtime(self.mtime)

        self.content_type: str = info.get_content_type() or ""
        if self.is_dir:
            self.type_display = "Folder"
        elif self.content_type:
            self.type_display = Gio.content_type_get_description(self.content_type)
        else:
            self.type_display = "File"

        self.gicon: Gio.Icon = info.get_icon() or Gio.ThemedIcon.new(
            "folder" if self.is_dir else "text-x-generic"
        )
        self.unix_mode: int = (
            info.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_MODE)
            if info.has_attribute(Gio.FILE_ATTRIBUTE_UNIX_MODE)
            else 0
        )
        self.symlink_target: str | None = (
            info.get_symlink_target() if self.is_symlink else None
        )
        self.trash_orig_path: str | None = (
            info.get_attribute_byte_string(Gio.FILE_ATTRIBUTE_TRASH_ORIG_PATH)
            if info.has_attribute(Gio.FILE_ATTRIBUTE_TRASH_ORIG_PATH)
            else None
        )

    @property
    def sort_name(self) -> str:
        return self.name.casefold()

    @property
    def extension(self) -> str:
        if self.is_dir:
            return ""
        return Path(self.name).suffix.lower()

    @property
    def is_image(self) -> bool:
        return self.content_type.startswith("image/")

    @property
    def is_text(self) -> bool:
        if not self.content_type:
            return False
        if self.content_type.startswith("text/"):
            return True
        return Gio.content_type_is_a(self.content_type, "text/plain")


def enumerate_directory(gfile: Gio.File) -> list[FileItem]:
    """Synchronously enumerate a Gio.File directory (intended to run in a worker thread)."""
    items: list[FileItem] = []
    enumerator = gfile.enumerate_children(
        FILE_QUERY_ATTRS,
        Gio.FileQueryInfoFlags.NONE,
        None,
    )
    try:
        while True:
            info = enumerator.next_file(None)
            if info is None:
                break
            child = enumerator.get_child(info)
            items.append(FileItem(child, info))
    finally:
        enumerator.close(None)
    return items


def query_file_item(gfile: Gio.File) -> FileItem | None:
    """Query a single Gio.File and return a FileItem, or None on error."""
    try:
        info = gfile.query_info(
            FILE_QUERY_ATTRS,
            Gio.FileQueryInfoFlags.NONE,
            None,
        )
        return FileItem(gfile, info)
    except GLib.Error:
        return None
