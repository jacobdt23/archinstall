"""Keyboard shortcuts and window-state toggle helpers."""

from libqtile.config import Key
from libqtile.lazy import lazy

from modules import groups, layouts, settings

MOD = settings.MOD
DIRECTIONS = ("Left", "Right", "Down", "Up")


def toggle_floating_or_tile(qtile_inst) -> None:
    """Toggle the focused window between floating and tiled, exiting fullscreen cleanly."""
    win = qtile_inst.current_window
    if not win:
        return
    if win.fullscreen:
        win.fullscreen = False
        win.floating = True
    else:
        win.toggle_floating()


def toggle_fullscreen_clean(qtile_inst) -> None:
    """Toggle fullscreen while keeping tiled state consistent on exit."""
    win = qtile_inst.current_window
    if not win:
        return
    if win.fullscreen:
        win.fullscreen = False
        win.floating = False
    else:
        win.fullscreen = True


def _build_directional_keys() -> list[Key]:
    result: list[Key] = []
    for direction in DIRECTIONS:
        d = direction.lower()
        result.extend([
            Key([MOD], direction, getattr(lazy.layout, d)(), desc=f"Move focus {d}"),
            Key([MOD, "shift"], direction, getattr(lazy.layout, f"shuffle_{d}")(), desc=f"Shuffle window {d}"),
            Key([MOD, "control"], direction, getattr(lazy.layout, f"grow_{d}")(), desc=f"Grow window {d}"),
        ])
    return result


def _build_volume_keys() -> list[Key]:
    actions = [
        ("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+", "Volume up", [([], "XF86AudioRaiseVolume"), ([MOD], "equal")]),
        ("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-", "Volume down", [([], "XF86AudioLowerVolume"), ([MOD], "minus")]),
        ("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle", "Mute volume", [([], "XF86AudioMute"), ([MOD], "BackSpace")]),
    ]
    return [
        Key(mods, key, lazy.spawn(cmd), desc=desc)
        for cmd, desc, bindings in actions
        for mods, key in bindings
    ]


def _build_group_keys() -> list[Key]:
    result: list[Key] = []
    for grp in groups.groups:
        key_name = "0" if grp.name == "10" else grp.name
        result.extend([
            Key([MOD], key_name, lazy.function(groups.go_to_group(grp.name)), desc=f"Switch to group {grp.name}"),
            Key([MOD, "shift"], key_name, lazy.window.togroup(grp.name, switch_group=False), desc=f"Move window to group {grp.name}"),
        ])
    return result


keys: list[Key] = [
    # Application launcher (Super tap via keyd F24, plus Super+Space/R/D)
    Key([], "F24", lazy.spawn(settings.LAUNCHER), desc="Open Rofi app launcher with Super tap"),
    *[
        Key([MOD], key, lazy.spawn(settings.LAUNCHER), desc="Open Rofi app launcher")
        for key in ("space", "r", "d")
    ],

    # Core applications (Orbit Suite + LazyVim)
    Key([MOD], "Return", lazy.spawn(settings.TERMINAL), desc="Launch Orbit Term"),
    Key([MOD], "e", lazy.spawn(settings.FILE_MANAGER), desc="Launch Orbit Files"),
    Key([MOD], "n", lazy.spawn(settings.EDITOR), desc="Launch Orbit Edit (LazyVim)"),
    Key([MOD, "shift"], "d", lazy.spawn("rofi -show drun"), desc="Rofi fallback launcher"),
    Key([MOD], "b", lazy.spawn(settings.BROWSER), desc="Launch Brave Browser"),
    Key([MOD], "w", lazy.spawn(settings.WELCOME_APP), desc="Open HyprFrost Welcome Center"),
    Key([MOD], "c", lazy.window.kill(), desc="Close focused window"),

    # Window state & monitor focus
    Key([MOD], "v", lazy.function(toggle_floating_or_tile), desc="Toggle floating / tile window"),
    Key([MOD], "f", lazy.function(toggle_fullscreen_clean), desc="Toggle fullscreen / tile"),
    Key([MOD], "Tab", lazy.next_screen(), desc="Focus next monitor"),

    # Tiling layout controls
    Key([MOD], "j", lazy.layout.toggle_split(), desc="Toggle split"),
    Key([MOD, "control"], "space", lazy.function(layouts.cycle_all_screens_layout), desc="Cycle layout on all screens"),
    *_build_directional_keys(),
    Key([MOD, "control"], "n", lazy.layout.normalize(), desc="Reset window sizes"),

    # Volume & media keys
    *_build_volume_keys(),

    # Screenshots (Flameshot wrapper)
    Key([], "Print", lazy.spawn(settings.SCREENSHOT_CMD), desc="Flameshot GUI"),
    Key(["shift"], "Print", lazy.spawn(f"{settings.SCREENSHOT_CMD} full"), desc="Full screenshot"),
    Key([MOD], "Print", lazy.spawn(settings.SCREENSHOT_CMD), desc="Flameshot GUI"),
    Key([MOD, "shift"], "s", lazy.spawn(settings.SCREENSHOT_CMD), desc="Flameshot GUI"),
    Key([MOD, "control"], "s", lazy.spawn(f"{settings.SCREENSHOT_CMD} config"), desc="Flameshot config"),

    # Clipboard & keybind help
    Key([MOD, "shift"], "v", lazy.spawn(settings.CLIPBOARD_CMD), desc="Clipboard history"),
    Key([MOD], "k", lazy.spawn(["notify-send", "Keybinds", settings.KEYBINDS_HELP_BODY]), desc="Show keybinds"),

    # Session management
    Key([MOD, "shift"], "r", lazy.reload_config(), desc="Reload Qtile Configuration"),
    Key([MOD, "shift"], "q", lazy.shutdown(), desc="Logout / Exit Qtile"),

    # Workspaces 1-10
    *_build_group_keys(),
]
