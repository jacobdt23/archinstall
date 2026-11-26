"""Mouse bindings and drag-to-float / drop-to-tile snapping."""

import types

from libqtile.config import Click, Drag
from libqtile.lazy import lazy
from libqtile.log_utils import logger

from modules import settings

MOD = settings.MOD
DRAG_THRESHOLD_PX = 5

DIALOG_WM_CLASSES = frozenset({
    "pavucontrol",
    "blueman-manager",
    "pinentry",
    "ssh-askpass",
    "confirmreset",
    "makebranch",
    "maketag",
    "branchdialog",
    "file_progress",
    "dialog",
    "download",
    "error",
    "notification",
})

GAME_CLASS_TOKENS = ("hogwarts", "steam_app")

_MOVE_BINDINGS = [
    ([], "Button2"),
    ([MOD], "Button1"),
    ([MOD], "Button2"),
    (["mod1"], "Button1"),
    (["mod1"], "Button2"),
]

_RESIZE_BINDINGS = [
    ([MOD], "Button3"),
    (["mod1"], "Button3"),
]

mouse = [
    *[
        Drag(mods, button, lazy.window.set_position_floating(), start=lazy.window.get_position())
        for mods, button in _MOVE_BINDINGS
    ],
    *[
        Drag(mods, button, lazy.window.set_size_floating(), start=lazy.window.get_size())
        for mods, button in _RESIZE_BINDINGS
    ],
    Click([MOD], "Button1", lazy.window.bring_to_front()),
    Click([MOD], "Button2", lazy.window.bring_to_front()),
]


def _is_drag_binding(qtile_inst, button_code: int, modmask: int) -> bool:
    return any(
        isinstance(m, Drag) and m.modmask == modmask
        for m in qtile_inst._mouse_map.get(button_code, [])
    )


def _find_screen_at(qtile_inst, x: int, y: int):
    for scr in qtile_inst.screens:
        if scr.x <= x < scr.x + scr.width and scr.y <= y < scr.y + scr.height:
            return scr
    return None


def _find_tiled_window_at(group, exclude_win, x: int, y: int):
    for win in group.windows:
        if win is exclude_win or getattr(win, "floating", False):
            continue
        wx, wy = win.get_position()
        ww, wh = win.get_size()
        if wx <= x < wx + ww and wy <= y < wy + wh:
            return win
    return None


def _snap_to_screen_and_target(qtile_inst, win, drop_xy: tuple[int, int]) -> None:
    """Move dragged window to the screen under drop_xy and orient BSP split."""
    dx, dy = drop_xy
    scr = _find_screen_at(qtile_inst, dx, dy)
    if not scr:
        return

    if scr.group and win.group != scr.group:
        win.togroup(scr.group.name)

    grp = scr.group
    if not grp or not hasattr(grp, "layout"):
        return

    lay = grp.layout
    target_win = _find_tiled_window_at(grp, win, dx, dy)
    if target_win is None or not hasattr(lay, "get_node"):
        return

    node = lay.get_node(target_win)
    if node is not None:
        lay.current = node
    wx, wy = target_win.get_position()
    ww, wh = target_win.get_size()
    rel_x = (dx - wx) / max(ww, 1)
    rel_y = (dy - wy) / max(wh, 1)
    # Set BSP split side before win.floating = False triggers add_client()
    lay.lower_right = (rel_x + rel_y) >= 1.0


def _finalize_dropped_window(qtile_inst, win, drop_xy: tuple[int, int] | None) -> None:
    try:
        wm_classes = [c.lower() for c in (win.get_wm_class() or [])]
        if any(cls in DIALOG_WM_CLASSES for cls in wm_classes):
            win.bring_to_front()
            return

        is_game = any(token in cls for cls in wm_classes for token in GAME_CLASS_TOKENS)
        if getattr(win, "_drag_was_fullscreen", False) or is_game:
            win.fullscreen = True
            win.floating = False
            win.bring_to_front()
            return

        if drop_xy:
            _snap_to_screen_and_target(qtile_inst, win, drop_xy)

        win.floating = False
        # Restore BSP's default split direction after retiling completes
        if win.group and hasattr(win.group, "layout") and hasattr(win.group.layout, "lower_right"):
            win.group.layout.lower_right = True
        win.focus(warp=False)
        win.bring_to_front()
    except Exception:
        logger.debug("Drag-snap drop finalization skipped for window", exc_info=True)


def setup_drag_snap(qtile_inst) -> None:
    """Patch Qtile pointer handlers so dragging tiled windows floats and re-tiles on drop."""
    if not qtile_inst:
        return

    orig_click = qtile_inst.__class__.process_button_click
    orig_release = qtile_inst.__class__.process_button_release
    orig_motion = qtile_inst.__class__.process_button_motion

    def patched_click(self, button_code, modmask, x, y):
        if button_code in (4, 5, 6, 7) or not _is_drag_binding(self, button_code, modmask):
            return orig_click(self, button_code, modmask, x, y)

        win = self.current_window
        was_fs = bool(win and getattr(win, "fullscreen", False))
        if was_fs:
            win.fullscreen = False

        handled = orig_click(self, button_code, modmask, x, y)
        if self._drag is not None and win:
            self._pending_drag_window = win
            self._active_drag_window = None
            self._last_drag_xy = (x, y)
            win._drag_was_fullscreen = was_fs
            win._drag_was_tiled = not getattr(win, "floating", False)
        elif was_fs and win:
            win.fullscreen = True
        return handled

    def patched_motion(self, x, y):
        if self._drag is not None:
            self._last_drag_xy = (x, y)
            pending = getattr(self, "_pending_drag_window", None)
            if pending is not None:
                ox, oy = self._drag[0], self._drag[1]
                if abs(x - ox) > DRAG_THRESHOLD_PX or abs(y - oy) > DRAG_THRESHOLD_PX:
                    self._pending_drag_window = None
                    self._active_drag_window = pending
                    try:
                        if not getattr(pending, "floating", False):
                            pending.floating = True
                        pending.bring_to_front()
                    except Exception:
                        logger.debug("Failed promoting dragged window to float", exc_info=True)

        handled = orig_motion(self, x, y)
        active = getattr(self, "_active_drag_window", None)
        if active:
            try:
                active.bring_to_front()
            except Exception:
                logger.debug("Failed bringing dragged window to front", exc_info=True)
        return handled

    def patched_release(self, button_code, modmask):
        self._pending_drag_window = None
        win = getattr(self, "_active_drag_window", None)
        was_drag = (self._drag is not None) and (win is not None)
        drop_xy = getattr(self, "_last_drag_xy", None)
        handled = orig_release(self, button_code, modmask)

        if was_drag and win:
            self._active_drag_window = None
            _finalize_dropped_window(self, win, drop_xy)
        return handled

    qtile_inst.process_button_click = types.MethodType(patched_click, qtile_inst)
    qtile_inst.process_button_release = types.MethodType(patched_release, qtile_inst)
    qtile_inst.process_button_motion = types.MethodType(patched_motion, qtile_inst)
    qtile_inst._drag_snap_installed = True
