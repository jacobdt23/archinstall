"""Shared GTK 4 / Libadwaita bootstrap helpers for Orbit Suite."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, Gtk

WINDOWCONTROLS_FIX_CSS = """
windowcontrols button.close,
windowcontrols button.maximize,
windowcontrols button.minimize {
    background-image: none;
    background-color: alpha(@window_fg_color, 0.08);
    color: @window_fg_color;
    border-radius: 9999px;
    min-width: 24px;
    min-height: 24px;
    padding: 0;
    margin: 0 3px;
    box-shadow: none;
    border: none;
}

windowcontrols button.close:hover,
windowcontrols button.maximize:hover,
windowcontrols button.minimize:hover,
windowcontrols button.close:active,
windowcontrols button.maximize:active,
windowcontrols button.minimize:active {
    background-image: none;
    background-color: alpha(@window_fg_color, 0.18);
    color: @window_fg_color;
}

windowcontrols button.close:hover,
windowcontrols button.close:active {
    background-color: alpha(#f7768e, 0.85);
    color: #ffffff;
}

windowcontrols button.close:backdrop,
windowcontrols button.maximize:backdrop,
windowcontrols button.minimize:backdrop {
    background-image: none;
    background-color: alpha(@window_fg_color, 0.04);
    color: alpha(@window_fg_color, 0.55);
}
"""


def load_css_string(css: str) -> None:
    """Register application CSS and window-control button fixes on the default display."""
    provider = Gtk.CssProvider()
    provider.load_from_string(WINDOWCONTROLS_FIX_CSS + "\n" + css)
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )
