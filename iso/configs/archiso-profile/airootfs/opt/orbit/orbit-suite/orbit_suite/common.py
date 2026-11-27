"""Shared GTK 4 / Libadwaita Dracula bootstrap helpers for Orbit Suite."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from pathlib import Path

from gi.repository import Gdk, Gtk

DRACULA_BASE_CSS = """
@define-color accent_color #bd93f9;
@define-color accent_bg_color #bd93f9;
@define-color accent_fg_color #21222c;
@define-color window_bg_color #282a36;
@define-color window_fg_color #f8f8f2;
@define-color view_bg_color #282a36;
@define-color view_fg_color #f8f8f2;
@define-color headerbar_bg_color #21222c;
@define-color headerbar_fg_color #f8f8f2;
@define-color headerbar_border_color #44475a;
@define-color sidebar_bg_color #21222c;
@define-color sidebar_fg_color #f8f8f2;
@define-color card_bg_color #343746;
@define-color card_fg_color #f8f8f2;
@define-color popover_bg_color #21222c;
@define-color popover_fg_color #f8f8f2;
@define-color dialog_bg_color #282a36;
@define-color dialog_fg_color #f8f8f2;

headerbar windowcontrols > button.close,
headerbar windowcontrols > button.maximize,
headerbar windowcontrols > button.minimize,
windowcontrols > button.close,
windowcontrols > button.maximize,
windowcontrols > button.minimize {
    background-color: transparent;
    background-image: none;
    border: none;
    box-shadow: none;
    padding: 0 3px;
    margin: 0;
    min-width: 22px;
    min-height: 22px;
}

headerbar windowcontrols > button.close > image,
headerbar windowcontrols > button.maximize > image,
headerbar windowcontrols > button.minimize > image,
windowcontrols > button.close > image,
windowcontrols > button.maximize > image,
windowcontrols > button.minimize > image {
    background-image: none;
    border-radius: 9999px;
    min-width: 16px;
    min-height: 16px;
    padding: 0;
    color: transparent;
    -gtk-icon-size: 12px;
}

headerbar windowcontrols > button.minimize > image,
windowcontrols > button.minimize > image { background-color: #ffb86c; }

headerbar windowcontrols > button.maximize > image,
windowcontrols > button.maximize > image { background-color: #50fa7b; }

headerbar windowcontrols > button.close > image,
windowcontrols > button.close > image { background-color: #ff5555; }

headerbar windowcontrols > button.minimize:hover > image,
windowcontrols > button.minimize:hover > image { background-color: #ffb86c; color: #21222c; }

headerbar windowcontrols > button.maximize:hover > image,
windowcontrols > button.maximize:hover > image { background-color: #50fa7b; color: #21222c; }

headerbar windowcontrols > button.close:hover > image,
windowcontrols > button.close:hover > image { background-color: #ff5555; color: #21222c; }

headerbar windowcontrols > button.close:backdrop > image,
headerbar windowcontrols > button.maximize:backdrop > image,
headerbar windowcontrols > button.minimize:backdrop > image,
windowcontrols > button.close:backdrop > image,
windowcontrols > button.maximize:backdrop > image,
windowcontrols > button.minimize:backdrop > image {
    background-color: #6272a4;
    color: transparent;
}
"""


def load_css_string(css: str) -> None:
    """Register Dracula GTK4/Libadwaita CSS plus any active dynamic Orbit wallpaper palette."""
    dynamic_path = Path.home() / ".config" / "orbit" / "theme.css"
    dynamic_css = dynamic_path.read_text(encoding="utf-8") if dynamic_path.is_file() else ""
    provider = Gtk.CssProvider()
    provider.load_from_string(DRACULA_BASE_CSS + "\n" + css + "\n" + dynamic_css)
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )
