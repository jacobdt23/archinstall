"""File operations and clipboard management for Orbit Files."""

from __future__ import annotations

import os
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from gi.repository import Gdk, Gio, GLib

OnComplete = Callable[[bool, str], None]


@dataclass
class FileClipboard:
    """Tracks copied or cut files inside the application."""

    uris: list[str] = field(default_factory=list)
    is_cut: bool = False

    def set_files(self, gfiles: list[Gio.File], is_cut: bool = False) -> None:
        self.uris = [f.get_uri() for f in gfiles]
        self.is_cut = is_cut

        # Also publish to the system clipboard so external apps can paste paths/files.
        display = Gdk.Display.get_default()
        if display is not None and gfiles:
            clipboard = display.get_clipboard()
            try:
                file_list = Gdk.FileList.new_from_list(gfiles)
                provider = Gdk.ContentProvider.new_for_value(file_list)
                clipboard.set_content(provider)
            except Exception:
                # Fallback to plain text paths if FileList fails
                paths = "\n".join(f.get_path() or f.get_uri() for f in gfiles)
                clipboard.set(paths)

    def clear(self) -> None:
        self.uris.clear()
        self.is_cut = False

    @property
    def has_files(self) -> bool:
        return bool(self.uris)

    def get_gfiles(self) -> list[Gio.File]:
        return [Gio.File.new_for_uri(u) for u in self.uris]


def unique_destination(dest_dir: Path, name: str) -> Path:
    """Return a non-colliding destination path inside dest_dir."""
    candidate = dest_dir / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    # Keep dotfiles intact when generating copy names
    if name.startswith(".") and name.count(".") == 1:
        stem = name
        suffix = ""

    idx = 1
    while True:
        label = " (copy)" if idx == 1 else f" (copy {idx})"
        candidate = dest_dir / f"{stem}{label}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def _run_in_thread(
    worker: Callable[[], str],
    on_complete: OnComplete | None = None,
) -> None:
    def _target() -> None:
        try:
            message = worker()
            if on_complete is not None:
                GLib.idle_add(on_complete, True, message)
        except Exception as exc:
            if on_complete is not None:
                GLib.idle_add(on_complete, False, str(exc))

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()


def copy_files(
    sources: list[Gio.File],
    dest_dir: Gio.File,
    on_complete: OnComplete | None = None,
) -> None:
    """Copy files/directories into dest_dir in a background thread."""

    def _work() -> str:
        dest_path_str = dest_dir.get_path()
        if not dest_path_str:
            raise OSError("Destination must be a local folder.")
        dest_path = Path(dest_path_str)
        if not dest_path.is_dir():
            raise OSError(f"Destination is not a folder: {dest_path}")

        count = 0
        for src in sources:
            src_path_str = src.get_path()
            if not src_path_str:
                # Fallback to Gio.File.copy for non-local files
                basename = src.get_basename() or "file"
                target = Gio.File.new_for_path(str(unique_destination(dest_path, basename)))
                src.copy(target, Gio.FileCopyFlags.NONE, None, None)
                count += 1
                continue

            src_path = Path(src_path_str)
            target = unique_destination(dest_path, src_path.name)
            if src_path.is_dir() and not src_path.is_symlink():
                # Prevent copying a directory into itself
                try:
                    target.resolve().relative_to(src_path.resolve())
                    raise OSError(f"Cannot copy '{src_path.name}' into itself.")
                except ValueError:
                    pass
                shutil.copytree(src_path, target, symlinks=True)
            else:
                shutil.copy2(src_path, target, follow_symlinks=False)
            count += 1

        noun = "item" if count == 1 else "items"
        return f"Copied {count} {noun}"

    _run_in_thread(_work, on_complete)


def move_files(
    sources: list[Gio.File],
    dest_dir: Gio.File,
    on_complete: OnComplete | None = None,
) -> None:
    """Move files/directories into dest_dir in a background thread."""

    def _work() -> str:
        dest_path_str = dest_dir.get_path()
        if not dest_path_str:
            raise OSError("Destination must be a local folder.")
        dest_path = Path(dest_path_str)
        if not dest_path.is_dir():
            raise OSError(f"Destination is not a folder: {dest_path}")

        count = 0
        for src in sources:
            src_path_str = src.get_path()
            if not src_path_str:
                basename = src.get_basename() or "file"
                target = Gio.File.new_for_path(str(unique_destination(dest_path, basename)))
                src.move(target, Gio.FileCopyFlags.NONE, None, None)
                count += 1
                continue

            src_path = Path(src_path_str)
            if src_path.parent.resolve() == dest_path.resolve():
                # Already in this directory; skip no-op move
                continue

            target = unique_destination(dest_path, src_path.name)
            if src_path.is_dir() and not src_path.is_symlink():
                try:
                    target.resolve().relative_to(src_path.resolve())
                    raise OSError(f"Cannot move '{src_path.name}' into itself.")
                except ValueError:
                    pass
            shutil.move(str(src_path), str(target))
            count += 1

        if count == 0:
            return "No items moved"
        noun = "item" if count == 1 else "items"
        return f"Moved {count} {noun}"

    _run_in_thread(_work, on_complete)


def trash_files(
    targets: list[Gio.File],
    on_complete: OnComplete | None = None,
) -> None:
    """Move files to the system Trash in a background thread."""

    def _work() -> str:
        count = 0
        for gfile in targets:
            gfile.trash(None)
            count += 1
        noun = "item" if count == 1 else "items"
        return f"Moved {count} {noun} to Trash"

    _run_in_thread(_work, on_complete)


def restore_from_trash(
    targets: list[Gio.File],
    on_complete: OnComplete | None = None,
) -> None:
    """Restore trashed items back to their original paths."""

    def _work() -> str:
        count = 0
        for gfile in targets:
            info = gfile.query_info(
                Gio.FILE_ATTRIBUTE_TRASH_ORIG_PATH,
                Gio.FileQueryInfoFlags.NONE,
                None,
            )
            orig_path = info.get_attribute_byte_string(Gio.FILE_ATTRIBUTE_TRASH_ORIG_PATH)
            if not orig_path:
                raise OSError(f"No original path recorded for {gfile.get_basename()}")
            dest_path = Path(orig_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if dest_path.exists():
                dest_path = unique_destination(dest_path.parent, dest_path.name)
            dest_gfile = Gio.File.new_for_path(str(dest_path))
            gfile.move(dest_gfile, Gio.FileCopyFlags.NONE, None, None)
            count += 1
        noun = "item" if count == 1 else "items"
        return f"Restored {count} {noun} from Trash"

    _run_in_thread(_work, on_complete)


def delete_files_permanently(
    targets: list[Gio.File],
    on_complete: OnComplete | None = None,
) -> None:
    """Permanently delete files and directories in a background thread."""

    def _work() -> str:
        count = 0
        for gfile in targets:
            path_str = gfile.get_path()
            if path_str:
                p = Path(path_str)
                if p.is_dir() and not p.is_symlink():
                    shutil.rmtree(p)
                else:
                    p.unlink()
            else:
                gfile.delete(None)
            count += 1
        noun = "item" if count == 1 else "items"
        return f"Permanently deleted {count} {noun}"

    _run_in_thread(_work, on_complete)


def rename_file(gfile: Gio.File, new_name: str) -> Gio.File:
    """Rename a file or directory synchronously and return the new Gio.File."""
    cleaned = new_name.strip()
    if not cleaned or "/" in cleaned or cleaned in (".", ".."):
        raise ValueError("Invalid file or folder name.")
    return gfile.set_display_name(cleaned, None)


def create_folder(parent_dir: Gio.File, name: str) -> Gio.File:
    """Create a new subfolder inside parent_dir."""
    cleaned = name.strip()
    if not cleaned or "/" in cleaned or cleaned in (".", ".."):
        raise ValueError("Invalid folder name.")
    child = parent_dir.get_child(cleaned)
    child.make_directory(None)
    return child


def create_empty_file(parent_dir: Gio.File, name: str) -> Gio.File:
    """Create an empty file inside parent_dir."""
    cleaned = name.strip()
    if not cleaned or "/" in cleaned or cleaned in (".", ".."):
        raise ValueError("Invalid file name.")
    path_str = parent_dir.get_path()
    if not path_str:
        raise OSError("Cannot create file in non-local location.")
    target = Path(path_str) / cleaned
    if target.exists():
        raise FileExistsError(f"'{cleaned}' already exists.")
    target.touch(exist_ok=False)
    return Gio.File.new_for_path(str(target))


def get_folder_stats(path: Path, max_entries: int = 2000) -> tuple[int, int, bool]:
    """Return (item_count, total_bytes, truncated) for quick folder summaries."""
    count = 0
    total = 0
    truncated = False
    try:
        with os.scandir(path) as it:
            for entry in it:
                count += 1
                try:
                    if not entry.is_dir(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                except OSError:
                    pass
                if count >= max_entries:
                    truncated = True
                    break
    except OSError:
        pass
    return count, total, truncated
