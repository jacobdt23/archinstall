"""Entry point for Orbit Files."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Adw", "1")
    gi.require_version("GdkPixbuf", "2.0")

    from orbit_files.app import OrbitFilesApp

    app = OrbitFilesApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
