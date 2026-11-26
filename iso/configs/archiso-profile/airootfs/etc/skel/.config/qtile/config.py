"""Qtile window manager configuration entrypoint."""

from modules import settings

settings.apply_environment()

# Import in dependency order so Qtile's submodule reloader updates cleanly
from modules import (  # noqa: E402, F401
    bar as _bar,
    groups as _groups,
    hooks as _hooks,
    keys as _keys,
    layouts as _layouts,
    mouse as _mouse,
)

groups = _groups.groups
layouts = _layouts.layouts
floating_layout = _layouts.floating_layout
keys = _keys.keys
screens = _bar.screens
mouse = _mouse.mouse

widget_defaults = settings.WIDGET_DEFAULTS
extension_defaults = settings.EXTENSION_DEFAULTS
wl_input_rules = settings.WL_INPUT_RULES

dgroups_key_binder = settings.QTILE_BEHAVIOR["dgroups_key_binder"]
dgroups_app_rules = settings.QTILE_BEHAVIOR["dgroups_app_rules"]
follow_mouse_focus = settings.QTILE_BEHAVIOR["follow_mouse_focus"]
bring_front_click = settings.QTILE_BEHAVIOR["bring_front_click"]
floats_kept_above = settings.QTILE_BEHAVIOR["floats_kept_above"]
cursor_warp = settings.QTILE_BEHAVIOR["cursor_warp"]
auto_fullscreen = settings.QTILE_BEHAVIOR["auto_fullscreen"]
focus_on_window_activation = settings.QTILE_BEHAVIOR["focus_on_window_activation"]
reconfigure_screens = settings.QTILE_BEHAVIOR["reconfigure_screens"]
auto_minimize = settings.QTILE_BEHAVIOR["auto_minimize"]
wmname = settings.QTILE_BEHAVIOR["wmname"]
