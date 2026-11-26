"""Workspace (group) definitions and multi-monitor navigation helpers."""

from libqtile.config import Group

from modules import settings

groups = [Group(name, label=name) for name in settings.GROUP_NAMES]


def go_to_group(name: str):
    """Switch to the target group and focus its assigned monitor (1-5 left, 6-10 right)."""

    def _inner(qtile_inst) -> None:
        target_screen = 0 if int(name) <= 5 else 1
        if len(qtile_inst.screens) > target_screen:
            qtile_inst.to_screen(target_screen)
        qtile_inst.groups_map[name].toscreen()

    return _inner
