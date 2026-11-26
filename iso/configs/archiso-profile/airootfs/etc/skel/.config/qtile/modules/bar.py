"""Top status bar, pill decorations, custom widget helpers, and screens."""

import os
import shutil

from libqtile import bar
from libqtile.config import Screen
from libqtile.lazy import lazy

from modules import settings

try:
    from qtile_extras import widget
    from qtile_extras.widget.decorations import RectDecoration

    HAS_EXTRAS = True
except ImportError:
    from libqtile import widget

    HAS_EXTRAS = False
    RectDecoration = None

QUICK_LAUNCHERS = [
    ("󰞷", settings.TERMINAL),
    ("󰉋", settings.FILE_MANAGER),
    ("󰈹", settings.BROWSER),
    ("󰚩", "antigravity"),
]


def pill_decor(
    group: bool = True,
    colour: str | None = None,
    line_colour: str | None = None,
    radius: int = 8,
) -> dict:
    """Return qtile-extras rounded pill decoration kwargs when available."""
    if not HAS_EXTRAS or RectDecoration is None:
        return {}
    colors = settings.COLORS
    return {
        "decorations": [
            RectDecoration(
                colour=colour or colors["pill_bg"],
                radius=radius,
                filled=True,
                padding_y=3,
                line_width=1,
                line_colour=line_colour or colors["pill_border"],
                group=group,
            )
        ]
    }


def truncate_window_title(text: str, max_len: int = 25) -> str:
    """Truncate window titles before Qtile escapes XML/Pango entities.

    Using WindowName's max_chars slices *after* markup escaping, which can cut
    entities like '&apos;' in half and trigger parse_markup() warnings.
    """
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"


def get_disk_status() -> str:
    """Return free root disk space and used percentage for GenPollText."""
    try:
        total, used, free = shutil.disk_usage("/")
        pct = (used / total) * 100
        if free >= 10**12:
            val = f"{free / (1024**4):.1f}T"
        elif free >= 10**9:
            val = f"{free / (1024**3):.0f}G"
        else:
            val = f"{free / (1024**2):.0f}M"
        return f"{val} ({pct:.0f}%)"
    except OSError:
        return "? (0%)"


def _sep(padding: int = 4):
    return widget.Sep(linewidth=0, padding=padding)


def _pill_textbox(
    text: str,
    *,
    foreground: str,
    fontsize: int = 11,
    padding: int = 6,
    font: str | None = None,
    mouse_callbacks: dict | None = None,
    group: bool = True,
    colour: str | None = None,
    line_colour: str | None = None,
):
    return widget.TextBox(
        text=text,
        foreground=foreground,
        font=font or settings.FONT,
        fontsize=fontsize,
        padding=padding,
        mouse_callbacks=mouse_callbacks or {},
        **pill_decor(group=group, colour=colour, line_colour=line_colour),
    )


def _hardware_pair(icon: str, icon_color: str, value_widget, command: str) -> list:
    cb = {"Button1": lazy.spawn(command)}
    return [
        _pill_textbox(
            icon,
            foreground=icon_color,
            fontsize=11,
            padding=4,
            mouse_callbacks=cb,
            group=True,
        ),
        value_widget,
        _sep(),
    ]


def build_top_bar() -> bar.Bar:
    """Build the unified top bar with Tokyo Night rounded pill styling."""
    colors = settings.COLORS
    btop_cb = {"Button1": lazy.spawn(settings.SYSTEM_MONITOR)}
    audio_cb = {"Button1": lazy.spawn(settings.AUDIO_MIXER)}

    widgets = [
        _sep(),
        # 1. Start / Brand Launcher
        _pill_textbox(
            "󰣇",
            foreground=colors["blue"],
            font=settings.FONT_BOLD,
            fontsize=12,
            padding=8,
            mouse_callbacks={"Button1": lazy.spawn(settings.LAUNCHER)},
            group=False,
            colour=colors["bg_alt"],
            line_colour=colors["blue"],
        ),
        _sep(),

        # 2. Workspaces 1-10
        widget.GroupBox(
            font=settings.FONT_BOLD,
            fontsize=10,
            margin_y=3,
            margin_x=2,
            padding_y=3,
            padding_x=6,
            borderwidth=1,
            active=colors["blue"],
            inactive=colors["fg_dim"],
            rounded=True,
            highlight_color=[colors["bg_alt"], colors["bg_alt"]],
            highlight_method="block",
            this_current_screen_border=colors["border_active"],
            block_highlight_text_color=colors["bar_bg"],
            visible_groups=list(settings.GROUP_NAMES),
            disable_drag=True,
            **pill_decor(group=False),
        ),
        _sep(),

        # 3. Quick App Launchers
        *[
            _pill_textbox(
                icon,
                foreground=colors["fg"],
                mouse_callbacks={"Button1": lazy.spawn(cmd)},
                group=True,
            )
            for icon, cmd in QUICK_LAUNCHERS
        ],
        _sep(),

        # 4. Current Layout
        widget.CurrentLayout(
            foreground=colors["purple"],
            font=settings.FONT_BOLD,
            fontsize=10,
            padding=6,
            **pill_decor(group=False),
        ),
        _sep(),

        # 5. Active Window Name
        widget.WindowName(
            foreground=colors["fg_dim"],
            padding=6,
            parse_text=truncate_window_title,
        ),
        widget.Spacer(),

        # 6. Center Date & Clock
        _pill_textbox(
            "󰥔 ",
            foreground=colors["cyan"],
            font=settings.FONT_BOLD,
            fontsize=12,
            padding=4,
            group=True,
        ),
        widget.Clock(
            format="%a, %b %d • %I:%M %p",
            foreground=colors["cyan"],
            font=settings.FONT_BOLD,
            fontsize=10,
            padding=6,
            mouse_callbacks={
                "Button1": lazy.spawn("notify-send 'Calendar' \"$(cal)\"", shell=True)
            },
            **pill_decor(group=True),
        ),
        _sep(),

        # 7. Media Chip
        _pill_textbox(
            "󰎆",
            foreground=colors["purple"],
            mouse_callbacks=audio_cb,
            group=False,
        ),
        widget.Spacer(),

        # 8. Utilities: Clipboard, Snip, Keys
        _pill_textbox(
            "󰅍",
            foreground=colors["fg"],
            mouse_callbacks={"Button1": lazy.spawn(settings.CLIPBOARD_CMD)},
            group=True,
        ),
        _pill_textbox(
            "󰄀",
            foreground=colors["fg"],
            mouse_callbacks={
                "Button1": lazy.spawn(settings.SCREENSHOT_CMD),
                "Button3": lazy.spawn(f"{settings.SCREENSHOT_CMD} config"),
            },
            group=True,
        ),
        _pill_textbox(
            "󰌌",
            foreground=colors["fg"],
            mouse_callbacks={
                "Button1": lazy.spawn(
                    ["notify-send", "Shortcuts", settings.KEYBINDS_HELP_BODY]
                )
            },
            group=True,
        ),
        _sep(),

        # 9. Hardware Status Area
        *_hardware_pair(
            "󰻠",
            colors["blue"],
            widget.CPU(
                format="{load_percent}%",
                foreground=colors["fg"],
                mouse_callbacks=btop_cb,
                **pill_decor(group=True),
            ),
            settings.SYSTEM_MONITOR,
        ),
        *_hardware_pair(
            "󰍛",
            colors["purple"],
            widget.Memory(
                measure_mem="G",
                format="{MemUsed:.1f}G ({MemPercent:.0f}%)",
                foreground=colors["fg"],
                mouse_callbacks=btop_cb,
                **pill_decor(group=True),
            ),
            settings.SYSTEM_MONITOR,
        ),
        *_hardware_pair(
            "󰋊",
            colors["yellow"],
            widget.GenPollText(
                func=get_disk_status,
                update_interval=30,
                foreground=colors["fg"],
                mouse_callbacks=btop_cb,
                **pill_decor(group=True),
            ),
            settings.SYSTEM_MONITOR,
        ),
        *_hardware_pair(
            "",
            colors["green"],
            widget.Volume(
                foreground=colors["fg"],
                mouse_callbacks=audio_cb,
                **pill_decor(group=True),
            ),
            settings.AUDIO_MIXER,
        ),

        # Network (Papirus Dark ethernet icon with connection editor launcher)
        widget.Image(
            filename=settings.NETWORK_ICON,
            margin=9,
            padding=6,
            mouse_callbacks={
                "Button1": lazy.spawn(settings.NET_GUI),
                "Button3": lazy.spawn(settings.NET_TUI),
            },
            **pill_decor(group=False),
        ),
        _sep(),

        # Power Button
        _pill_textbox(
            " ⏻ ",
            foreground=colors["red"],
            font=settings.FONT_BOLD,
            fontsize=12,
            padding=6,
            mouse_callbacks={"Button1": lazy.shutdown()},
            group=False,
            colour=colors["bg_alt"],
            line_colour=colors["red"],
        ),
        _sep(),
    ]

    return bar.Bar(
        widgets,
        38,
        background=colors["bar_bg"],
        opacity=1.0,
        margin=[6, 12, 0, 12],
        border_width=[1, 1, 1, 1],
        border_color=colors["bar_border"],
    )


_wallpaper = settings.WALLPAPER_PATH if os.path.isfile(settings.WALLPAPER_PATH) else None

screens = [
    Screen(
        top=build_top_bar(),
        wallpaper=_wallpaper,
        wallpaper_mode="fill",
    )
    for _ in range(settings.SCREEN_COUNT)
]
