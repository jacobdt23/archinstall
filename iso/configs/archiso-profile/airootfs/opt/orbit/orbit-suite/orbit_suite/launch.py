"""Orbit Launch — A keyboard-first GTK 4 + Libadwaita app launcher & command palette."""

from __future__ import annotations

import ast
import operator
import subprocess
import sys
from dataclasses import dataclass

from orbit_suite.common import load_css_string

from gi.repository import Adw, Gdk, Gio, Gtk

APP_ID = "dev.orbit.Launch"
APP_NAME = "Orbit Launch"

LAUNCH_CSS = """
.orbit-launch-entry {
    font-size: 1.15em;
    padding: 10px 14px;
    border-radius: 12px;
}
.orbit-launch-row {
    border-radius: 10px;
    padding: 6px 10px;
    margin: 2px 4px;
}
.orbit-launch-hint {
    opacity: 0.65;
}
"""

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_math(expr: str) -> str | None:
    """Safely evaluate a basic arithmetic expression using AST."""
    expr = expr.strip()
    if not expr:
        return None
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression")

    try:
        val = _eval(tree)
        if val.is_integer():
            return str(int(val))
        return f"{val:.6g}"
    except Exception:
        return None


@dataclass
class LaunchEntry:
    name: str
    description: str
    icon: Gio.Icon | None
    search_blob: str
    app_info: Gio.AppInfo | None = None
    shell_cmd: str | None = None
    copy_text: str | None = None


def load_desktop_apps() -> list[LaunchEntry]:
    """Load all visible desktop applications from XDG directories."""
    entries: list[LaunchEntry] = []
    seen: set[str] = set()
    for info in Gio.AppInfo.get_all():
        if not info.should_show():
            continue
        name = info.get_display_name() or info.get_name() or ""
        if not name:
            continue
        app_id = info.get_id() or name
        if app_id in seen:
            continue
        seen.add(app_id)

        desc = info.get_description() or ""
        keywords = ""
        if isinstance(info, Gio.DesktopAppInfo):
            kw = info.get_keywords()
            if kw:
                keywords = " ".join(kw)
            generic = info.get_generic_name() or ""
            if not desc and generic:
                desc = generic
        blob = f"{name} {desc} {keywords} {app_id}".casefold()
        entries.append(
            LaunchEntry(
                name=name,
                description=desc,
                icon=info.get_icon(),
                search_blob=blob,
                app_info=info,
            )
        )
    entries.sort(key=lambda e: e.name.casefold())
    return entries


def score_match(query: str, entry: LaunchEntry) -> int:
    """Return a relevance score (higher is better, 0 means no match)."""
    if not query:
        return 1
    q = query.casefold()
    name_cf = entry.name.casefold()
    if name_cf == q:
        return 100
    if name_cf.startswith(q):
        return 80
    if q in name_cf:
        return 60
    if q in entry.search_blob:
        return 40
    # Subsequence fuzzy match on name
    it = iter(name_cf)
    if all(ch in it for ch in q):
        return 20
    return 0


class OrbitLaunchWindow(Adw.ApplicationWindow):
    """Floating keyboard-driven launcher window."""

    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(620, 460)
        self.set_resizable(False)

        self._all_apps = load_desktop_apps()
        self._visible_entries: list[LaunchEntry] = []

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_margin_top(14)
        root.set_margin_bottom(12)
        root.set_margin_start(14)
        root.set_margin_end(14)

        self._entry = Gtk.SearchEntry()
        self._entry.add_css_class("orbit-launch-entry")
        self._entry.set_placeholder_text("Search apps…  (= math, > run command)")
        self._entry.connect("search-changed", lambda *_: self._refresh_results())
        self._entry.connect("activate", lambda *_: self._activate_selected())
        root.append(self._entry)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.add_css_class("navigation-sidebar")
        self._listbox.connect("row-activated", self._on_row_activated)
        scrolled.set_child(self._listbox)
        root.append(scrolled)

        hint = Gtk.Label(label="Enter: Launch  •  ↑/↓: Navigate  •  = calc  •  > run  •  Esc: Close")
        hint.add_css_class("caption")
        hint.add_css_class("orbit-launch-hint")
        root.append(hint)

        self.set_content(root)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

        self._refresh_results()
        self._entry.grab_focus()

    def _on_key_pressed(
        self,
        _ctrl: Gtk.EventControllerKey,
        keyval: int,
        _keycode: int,
        _state: Gdk.ModifierType,
    ) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        if keyval == Gdk.KEY_Down:
            self._move_selection(1)
            return True
        if keyval == Gdk.KEY_Up:
            self._move_selection(-1)
            return True
        return False

    def _move_selection(self, delta: int) -> None:
        if not self._visible_entries:
            return
        row = self._listbox.get_selected_row()
        idx = row.get_index() if row is not None else -1
        new_idx = max(0, min(len(self._visible_entries) - 1, idx + delta))
        target = self._listbox.get_row_at_index(new_idx)
        if target is not None:
            self._listbox.select_row(target)
            target.grab_focus()
            self._entry.grab_focus()
            self._entry.set_position(-1)

    def _refresh_results(self) -> None:
        while (child := self._listbox.get_first_child()) is not None:
            self._listbox.remove(child)

        raw = self._entry.get_text().strip()
        results: list[LaunchEntry] = []

        if raw.startswith("="):
            val = safe_eval_math(raw[1:])
            if val is not None:
                results.append(
                    LaunchEntry(
                        name=f"= {val}",
                        description="Press Enter to copy result to clipboard",
                        icon=Gio.ThemedIcon.new("accessories-calculator-symbolic"),
                        search_blob="",
                        copy_text=val,
                    )
                )
        elif raw.startswith(">"):
            cmd = raw[1:].strip()
            if cmd:
                results.append(
                    LaunchEntry(
                        name=f"Run: {cmd}",
                        description="Execute shell command in background",
                        icon=Gio.ThemedIcon.new("utilities-terminal-symbolic"),
                        search_blob="",
                        shell_cmd=cmd,
                    )
                )
        else:
            scored = [(score_match(raw, e), e) for e in self._all_apps]
            scored = [(s, e) for s, e in scored if s > 0]
            scored.sort(key=lambda pair: (-pair[0], pair[1].name.casefold()))
            results = [e for _, e in scored[:40]]

        self._visible_entries = results
        for entry in results:
            self._listbox.append(self._build_row(entry))

        first = self._listbox.get_row_at_index(0)
        if first is not None:
            self._listbox.select_row(first)

    def _build_row(self, entry: LaunchEntry) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.add_css_class("orbit-launch-row")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        if entry.icon is not None:
            img = Gtk.Image.new_from_gicon(entry.icon)
        else:
            img = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        img.set_pixel_size(32)
        box.append(img)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)

        title = Gtk.Label(label=entry.name)
        title.set_xalign(0.0)
        title.add_css_class("heading")
        title.set_ellipsize(3)
        text_box.append(title)

        if entry.description:
            sub = Gtk.Label(label=entry.description)
            sub.set_xalign(0.0)
            sub.add_css_class("caption")
            sub.add_css_class("dim-label")
            sub.set_ellipsize(3)
            text_box.append(sub)

        box.append(text_box)
        row.set_child(box)
        return row

    def _on_row_activated(self, _lb: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        idx = row.get_index()
        if 0 <= idx < len(self._visible_entries):
            self._execute_entry(self._visible_entries[idx])

    def _activate_selected(self) -> None:
        row = self._listbox.get_selected_row()
        if row is not None:
            self._on_row_activated(self._listbox, row)

    def _execute_entry(self, entry: LaunchEntry) -> None:
        if entry.copy_text is not None:
            display = Gdk.Display.get_default()
            if display is not None:
                display.get_clipboard().set(entry.copy_text)
        elif entry.shell_cmd is not None:
            subprocess.Popen(entry.shell_cmd, shell=True, start_new_session=True)
        elif entry.app_info is not None:
            try:
                entry.app_info.launch([], None)
            except Exception:
                pass
        self.close()


class OrbitLaunchApp(Adw.Application):
    """Orbit Launch application."""

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        load_css_string(LAUNCH_CSS)

    def do_activate(self) -> None:
        win = self.get_active_window()
        if win is None:
            win = OrbitLaunchWindow(self)
        win.present()


def main(argv: list[str] | None = None) -> int:
    app = OrbitLaunchApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
