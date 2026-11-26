"""Tiling layouts, floating rules, and layout-cycling helpers."""

from libqtile import layout
from libqtile.config import Match

from modules import settings

BORDER_THEME = {
    "border_width": 2,
    "border_focus": settings.COLORS["border_active"],
    "border_normal": settings.COLORS["border_inactive"],
}

LAYOUT_THEME = {
    **BORDER_THEME,
    "margin": 6,
}

layouts = [
    layout.Bsp(**LAYOUT_THEME, border_on_single=True, fair=False),
    layout.Columns(
        **LAYOUT_THEME,
        border_focus_stack=[settings.COLORS["purple"], settings.COLORS["blue"]],
        border_on_single=True,
    ),
    layout.Max(**LAYOUT_THEME),
    layout.Floating(**LAYOUT_THEME),
]

FLOAT_RULES = [
    *layout.Floating.default_float_rules,
    Match(wm_class="confirmreset"),
    Match(wm_class="makebranch"),
    Match(wm_class="maketag"),
    Match(wm_class="ssh-askpass"),
    Match(title="branchdialog"),
    Match(title="pinentry"),
    Match(wm_class="pavucontrol"),
    Match(wm_class="blueman-manager"),
    Match(wm_class="swappy"),
    Match(title="Missing Packages Detected"),
    Match(wm_class="Rofi"),
    Match(wm_class="hyprfrost-welcome"),
    Match(title="HyprFrost Welcome Center"),
]

floating_layout = layout.Floating(**BORDER_THEME, float_rules=FLOAT_RULES)


def cycle_all_screens_layout(qtile_inst) -> None:
    """Cycle the layout on all active monitors simultaneously in sync."""
    if not qtile_inst.current_group or not qtile_inst.current_group.layouts:
        return
    target_idx = (
        qtile_inst.current_group.current_layout + 1
    ) % len(qtile_inst.current_group.layouts)
    for screen in qtile_inst.screens:
        if screen.group:
            screen.group.use_layout(target_idx)
