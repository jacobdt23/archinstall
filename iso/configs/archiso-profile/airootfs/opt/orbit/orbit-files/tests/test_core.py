"""Unit tests for Orbit Files core models and file operations."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gio, GLib

from orbit_files import file_ops
from orbit_files.models import enumerate_directory, format_mode, format_size, query_file_item


class TestModelsAndFileOps(unittest.TestCase):
    def test_format_size(self) -> None:
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(512), "512 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")

    def test_format_mode(self) -> None:
        self.assertIn("755", format_mode(0o100755))

    def test_enumerate_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.txt").write_text("hello", encoding="utf-8")
            (root / ".hidden").write_text("secret", encoding="utf-8")
            (root / "sub").mkdir()

            items = enumerate_directory(Gio.File.new_for_path(str(root)))
            names = {item.name for item in items}
            self.assertEqual(names, {"alpha.txt", ".hidden", "sub"})

            hidden = next(i for i in items if i.name == ".hidden")
            self.assertTrue(hidden.is_hidden)
            sub = next(i for i in items if i.name == "sub")
            self.assertTrue(sub.is_dir)

            queried = query_file_item(Gio.File.new_for_path(str(root / "alpha.txt")))
            self.assertIsNotNone(queried)
            assert queried is not None
            self.assertEqual(queried.size, 5)
            self.assertTrue(queried.is_text)

    def test_create_rename_and_unique_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root_gfile = Gio.File.new_for_path(str(root))

            folder = file_ops.create_folder(root_gfile, "Docs")
            self.assertTrue((root / "Docs").is_dir())

            new_file = file_ops.create_empty_file(root_gfile, "notes.txt")
            self.assertTrue((root / "notes.txt").is_file())

            renamed = file_ops.rename_file(new_file, "readme.txt")
            self.assertEqual(Path(renamed.get_path()).name, "readme.txt")
            self.assertTrue((root / "readme.txt").is_file())

            # Unique destination collision handling
            cand = file_ops.unique_destination(root, "readme.txt")
            self.assertEqual(cand.name, "readme (copy).txt")

            # Folder stats
            count, total, truncated = file_ops.get_folder_stats(root)
            self.assertEqual(count, 2)
            self.assertEqual(total, 0)
            self.assertFalse(truncated)

            # Cleanup folder reference
            self.assertIsNotNone(folder)

    def test_copy_and_move_in_background(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src"
            dst_dir = root / "dst"
            src_dir.mkdir()
            dst_dir.mkdir()
            f1 = src_dir / "sample.txt"
            f1.write_text("orbit", encoding="utf-8")

            loop = GLib.MainLoop()
            result: dict[str, object] = {}

            def _on_copied(ok: bool, msg: str) -> bool:
                result["ok"] = ok
                result["msg"] = msg
                loop.quit()
                return False

            file_ops.copy_files(
                [Gio.File.new_for_path(str(f1))],
                Gio.File.new_for_path(str(dst_dir)),
                on_complete=_on_copied,
            )
            GLib.timeout_add(3000, loop.quit)
            loop.run()

            self.assertTrue(result.get("ok"))
            self.assertTrue((dst_dir / "sample.txt").is_file())
            self.assertTrue(f1.is_file())

            # Move to a third folder
            dst2 = root / "dst2"
            dst2.mkdir()
            result.clear()
            file_ops.move_files(
                [Gio.File.new_for_path(str(f1))],
                Gio.File.new_for_path(str(dst2)),
                on_complete=_on_copied,
            )
            GLib.timeout_add(3000, loop.quit)
            loop.run()

            self.assertTrue(result.get("ok"))
            self.assertTrue((dst2 / "sample.txt").is_file())
            self.assertFalse(f1.exists())


if __name__ == "__main__":
    unittest.main()
