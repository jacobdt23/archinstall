"""Qtile lifecycle hooks for autostart and drag-snap initialization."""

import os
import subprocess

from libqtile import hook, qtile

from modules import mouse, settings


@hook.subscribe.startup_once
def autostart() -> None:
    """Launch ~/.config/qtile/autostart.sh once per session."""
    script = settings.AUTOSTART_SCRIPT
    if os.path.isfile(script) and os.access(script, os.X_OK):
        subprocess.Popen(["/bin/bash", script], start_new_session=True)


@hook.subscribe.startup
def init_drag_snap() -> None:
    """Install or refresh drag-snap pointer hooks on startup and config reload."""
    if qtile:
        mouse.setup_drag_snap(qtile)
