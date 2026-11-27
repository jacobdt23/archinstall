"""Core settings, theme palette, paths, and general Qtile behavior."""

import os

# Wayland / toolkit environment defaults applied before Qtile subsystems load
def _bin(name: str) -> str:
    local = os.path.expanduser(f"~/.local/bin/{name}")
    return local if os.path.exists(local) else name


ENV_VARS = {
    "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
    "ELECTRON_OZONE_PLATFORM_HINT": "auto",
    "XCURSOR_SIZE": "24",
    "QT_QPA_PLATFORM": "wayland;xcb",
    "GDK_BACKEND": "wayland,x11,*",
    "XDG_CURRENT_DESKTOP": "X-Orbit-Qtile:Qtile",
    "XDG_SESSION_DESKTOP": "X-Orbit-Qtile",
    "EDITOR": _bin("orbit-nvim-cli"),
}


def apply_environment() -> None:
    """Export Wayland and toolkit environment variables into os.environ."""
    os.environ.update(ENV_VARS)


# Modifier & core applications (Orbit Suite + LazyVim)
MOD = "mod4"  # Super / Windows key
TERMINAL = _bin("orbit-term")
FILE_MANAGER = _bin("orbit-files")
EDITOR = _bin("orbit-nvim")
VIEWER = _bin("orbit-view")
BROWSER = "brave"
LAUNCHER = _bin("orbit-launch")
THEME_APP = _bin("orbit-theme")
SYSTEM_MONITOR = "kitty -e btop"
AUDIO_MIXER = "pavucontrol"
NET_GUI = "nm-connection-editor"
NET_TUI = "kitty -e nmtui"

# Paths & assets
SCREENSHOT_CMD = os.path.expanduser("~/.local/bin/hypr-screenshot")
CLIPBOARD_CMD = os.path.expanduser("~/.local/bin/hypr-clipboard")
WALLPAPER_PATH = os.path.expanduser("~/Pictures/Wallpapers/default.png")
AUTOSTART_SCRIPT = os.path.expanduser("~/.config/qtile/autostart.sh")
NETWORK_ICON = "/usr/share/icons/Papirus-Dark/16x16/devices/network-wired.svg"

KEYBINDS_HELP_BODY = (
    "Super+Return: Terminal\n"
    "Super+Space: App Launcher\n"
    "Super+E: Files\n"
    "Super+B: Browser\n"
    "Super+C: Close Window\n"
    "Super+Shift+Q: Exit"
)

# Typography
FONT = "JetBrainsMono Nerd Font"
FONT_BOLD = "JetBrainsMono Nerd Font Bold"

# Tokyo Night Frosted palette
COLORS = {
    "bar_bg": "#141622",          # Solid opaque bar background
    "bg_alt": "#1f2335",          # Slightly lighter pill surface
    "pill_bg": "#1a1b26",         # Standard pill container background
    "pill_border": "#292e42",     # Subtle dark pill border
    "fg": "#c0caf5",              # Primary text
    "fg_dim": "#565f89",          # Dim / muted text
    "blue": "#7aa2f7",            # Tokyo Night blue accent
    "purple": "#bb9af7",          # Purple accent
    "cyan": "#7dcfff",            # Cyan accent
    "green": "#9ece6a",           # Green accent
    "yellow": "#e0af68",          # Yellow
    "red": "#f7768e",             # Red / Warning
    "border_active": "#7aa2f7",
    "border_inactive": "#3b4261",
    "bar_border": "#3b4261",
}

SCREEN_COUNT = 2
GROUP_NAMES = [str(i) for i in range(1, 11)]

# Default widget & extension styling inherited by bar widgets
WIDGET_DEFAULTS = {
    "font": FONT,
    "fontsize": 10,
    "padding": 4,
}
EXTENSION_DEFAULTS = WIDGET_DEFAULTS.copy()

# Wayland libinput configuration (ignored on X11)
try:
    from libqtile.backend.wayland import InputConfig

    WL_INPUT_RULES = {
        "*": InputConfig(natural_scroll=False),
    }
except ImportError:
    WL_INPUT_RULES = None

# General Qtile window manager behavior
QTILE_BEHAVIOR = {
    "dgroups_key_binder": None,
    "dgroups_app_rules": [],
    "follow_mouse_focus": True,
    "bring_front_click": False,
    "floats_kept_above": True,
    "cursor_warp": False,
    "auto_fullscreen": False,
    "focus_on_window_activation": "smart",
    "reconfigure_screens": True,
    "auto_minimize": True,
    "wmname": "Qtile",
}
