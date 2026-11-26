"""Orbit Edit — A fast GTK 4 + Libadwaita text & code editor in Python."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from orbit_suite import __version__
from orbit_suite.common import load_css_string

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

APP_ID = "dev.orbit.Edit"
APP_NAME = "Orbit Edit"

EDIT_CSS = """
.orbit-editor-view {
    font-family: monospace;
    padding: 8px;
}
.orbit-editor-statusbar {
    border-top: 1px solid alpha(@borders, 0.6);
}
"""

_LANG_BY_EXT: dict[str, str] = {
    ".py": "Python",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".json": "JSON",
    ".css": "CSS",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".toml": "TOML",
    ".ini": "INI",
    ".conf": "Config",
    ".md": "Markdown",
    ".desktop": "Desktop Entry",
}

_KEYWORDS = (
    r"\b(?:def|class|return|import|from|as|if|elif|else|for|while|try|except|finally|"
    r"with|yield|lambda|pass|break|continue|True|False|None|async|await|fn|let|mut|"
    r"pub|struct|enum|impl|const|var|function|export|default|case|switch|in|not|and|or)\b"
)
_RE_COMMENT = re.compile(r"(#[^\n]*|//[^\n]*)")
_RE_STRING = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')
_RE_KEYWORD = re.compile(_KEYWORDS)
_RE_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_RE_SECTION = re.compile(r"^\[[^\]]+\]", re.MULTILINE)


class EditorTab(Gtk.Box):
    """Single document tab inside Orbit Edit."""

    __gsignals__ = {
        "meta-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, path: Path | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.path: Path | None = path
        self.modified: bool = False
        self._highlight_timeout: int | None = None

        self.buffer = Gtk.TextBuffer()
        self._setup_tags()
        self.buffer.connect("changed", self._on_buffer_changed)
        self.buffer.connect("mark-set", lambda *_: self.emit("meta-changed"))

        self.text_view = Gtk.TextView.new_with_buffer(self.buffer)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(14)
        self.text_view.set_right_margin(14)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_view.add_css_class("orbit-editor-view")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_child(self.text_view)
        self.append(scrolled)

        if path is not None and path.is_file():
            self.load_file(path)

    def _setup_tags(self) -> None:
        self._tag_keyword = self.buffer.create_tag("kw", foreground="#7aa2f7", weight=700)
        self._tag_string = self.buffer.create_tag("str", foreground="#9ece6a")
        self._tag_comment = self.buffer.create_tag("cmt", foreground="#7a8499", style=2)
        self._tag_number = self.buffer.create_tag("num", foreground="#ff9e64")
        self._tag_section = self.buffer.create_tag("sec", foreground="#bb9af7", weight=700)

    @property
    def language(self) -> str:
        if self.path is None:
            return "Plain Text"
        return _LANG_BY_EXT.get(self.path.suffix.lower(), "Plain Text")

    @property
    def title(self) -> str:
        base = self.path.name if self.path else "Untitled"
        return f"• {base}" if self.modified else base

    def load_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8", errors="replace")
        self.path = path
        self.buffer.set_text(text)
        self.modified = False
        self._apply_highlighting()
        self.emit("meta-changed")

    def save_to(self, path: Path) -> None:
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, True)
        path.write_text(text, encoding="utf-8")
        self.path = path
        self.modified = False
        self._apply_highlighting()
        self.emit("meta-changed")

    def set_word_wrap(self, enabled: bool) -> None:
        self.text_view.set_wrap_mode(
            Gtk.WrapMode.WORD_CHAR if enabled else Gtk.WrapMode.NONE
        )

    def get_cursor_stats(self) -> tuple[int, int, int]:
        """Return (line, column, word_count)."""
        it = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        line = it.get_line() + 1
        col = it.get_line_offset() + 1
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, False)
        words = len(text.split()) if text else 0
        return line, col, words

    def _on_buffer_changed(self, _buf: Gtk.TextBuffer) -> None:
        self.modified = True
        self.emit("meta-changed")
        if self._highlight_timeout is not None:
            GLib.source_remove(self._highlight_timeout)
        self._highlight_timeout = GLib.timeout_add(160, self._debounced_highlight)

    def _debounced_highlight(self) -> bool:
        self._highlight_timeout = None
        self._apply_highlighting()
        return False

    def _apply_highlighting(self) -> None:
        start, end = self.buffer.get_bounds()
        for tag in (
            self._tag_keyword,
            self._tag_string,
            self._tag_comment,
            self._tag_number,
            self._tag_section,
        ):
            self.buffer.remove_tag(tag, start, end)

        if self.language == "Plain Text":
            return

        text = self.buffer.get_text(start, end, False)
        if len(text) > 120_000:
            return

        def _tag_regex(pattern: re.Pattern[str], tag: Gtk.TextTag) -> None:
            for m in pattern.finditer(text):
                it_s = self.buffer.get_iter_at_offset(m.start())
                it_e = self.buffer.get_iter_at_offset(m.end())
                self.buffer.apply_tag(tag, it_s, it_e)

        _tag_regex(_RE_KEYWORD, self._tag_keyword)
        _tag_regex(_RE_NUMBER, self._tag_number)
        _tag_regex(_RE_SECTION, self._tag_section)
        _tag_regex(_RE_STRING, self._tag_string)
        _tag_regex(_RE_COMMENT, self._tag_comment)


class OrbitEditWindow(Adw.ApplicationWindow):
    """Main Orbit Edit window."""

    def __init__(self, app: Adw.Application, initial_files: list[Path] | None = None) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(940, 680)
        self._font_size = 11
        self._font_provider = Gtk.CssProvider()
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._font_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER + 1,
            )

        self._setup_actions()
        self._build_ui()
        self._apply_font_size()

        if initial_files:
            for p in initial_files:
                self.open_tab(p)
        else:
            self.open_tab(None)

    def _build_ui(self) -> None:
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        toolbar_view = Adw.ToolbarView()
        self._toast_overlay.set_child(toolbar_view)

        header = Adw.HeaderBar()

        open_btn = Gtk.Button.new_from_icon_name("document-open-symbolic")
        open_btn.set_tooltip_text("Open File (Ctrl+O)")
        open_btn.set_action_name("win.open")
        header.pack_start(open_btn)

        new_btn = Gtk.Button.new_from_icon_name("tab-new-symbolic")
        new_btn.set_tooltip_text("New Tab (Ctrl+T)")
        new_btn.set_action_name("win.new-tab")
        header.pack_start(new_btn)

        save_btn = Gtk.Button.new_with_label("Save")
        save_btn.add_css_class("suggested-action")
        save_btn.set_tooltip_text("Save (Ctrl+S)")
        save_btn.set_action_name("win.save")
        header.pack_end(save_btn)

        find_btn = Gtk.Button.new_from_icon_name("edit-find-symbolic")
        find_btn.set_tooltip_text("Find & Replace (Ctrl+F)")
        find_btn.set_action_name("win.toggle-find")
        header.pack_end(find_btn)

        menu = Gio.Menu()
        menu.append("Save As…", "win.save-as")
        menu.append("Word Wrap", "win.toggle-wrap")
        menu.append("Zoom In", "win.zoom-in")
        menu.append("Zoom Out", "win.zoom-out")
        menu.append("Reset Zoom", "win.zoom-reset")
        menu.append("About Orbit Edit", "win.about")
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        toolbar_view.add_top_bar(header)

        self._tab_view = Adw.TabView()
        self._tab_view.connect("notify::selected-page", lambda *_: self._sync_status())
        self._tab_view.connect("close-page", self._on_close_page)

        self._tab_bar = Adw.TabBar()
        self._tab_bar.set_view(self._tab_view)
        self._tab_bar.set_autohide(True)
        toolbar_view.add_top_bar(self._tab_bar)

        # Collapsible Find & Replace bar
        self._find_revealer = Gtk.Revealer()
        self._find_revealer.set_reveal_child(False)
        find_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        find_box.set_margin_top(6)
        find_box.set_margin_bottom(6)
        find_box.set_margin_start(10)
        find_box.set_margin_end(10)

        self._find_entry = Gtk.SearchEntry()
        self._find_entry.set_placeholder_text("Find…")
        self._find_entry.set_hexpand(True)
        self._find_entry.connect("activate", lambda *_: self._find_next())
        find_box.append(self._find_entry)

        self._replace_entry = Gtk.Entry()
        self._replace_entry.set_placeholder_text("Replace with…")
        self._replace_entry.set_hexpand(True)
        find_box.append(self._replace_entry)

        next_btn = Gtk.Button.new_with_label("Find Next")
        next_btn.connect("clicked", lambda *_: self._find_next())
        find_box.append(next_btn)

        rep_btn = Gtk.Button.new_with_label("Replace")
        rep_btn.connect("clicked", lambda *_: self._replace_one())
        find_box.append(rep_btn)

        rep_all_btn = Gtk.Button.new_with_label("Replace All")
        rep_all_btn.connect("clicked", lambda *_: self._replace_all())
        find_box.append(rep_all_btn)

        close_find = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_find.add_css_class("flat")
        close_find.connect("clicked", lambda *_: self._find_revealer.set_reveal_child(False))
        find_box.append(close_find)

        self._find_revealer.set_child(find_box)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.append(self._find_revealer)
        content_box.append(self._tab_view)
        toolbar_view.set_content(content_box)

        # Status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.add_css_class("orbit-editor-statusbar")
        status_bar.set_margin_top(4)
        status_bar.set_margin_bottom(4)
        status_bar.set_margin_start(12)
        status_bar.set_margin_end(12)

        self._status_left = Gtk.Label(label="")
        self._status_left.set_xalign(0.0)
        self._status_left.set_hexpand(True)
        self._status_left.add_css_class("caption")
        self._status_left.add_css_class("dim-label")
        status_bar.append(self._status_left)

        self._status_right = Gtk.Label(label="")
        self._status_right.set_xalign(1.0)
        self._status_right.add_css_class("caption")
        self._status_right.add_css_class("dim-label")
        status_bar.append(self._status_right)
        toolbar_view.add_bottom_bar(status_bar)

    def _setup_actions(self) -> None:
        actions = [
            ("new-tab", lambda *_: self.open_tab(None)),
            ("close-tab", self._act_close_tab),
            ("open", self._act_open),
            ("save", self._act_save),
            ("save-as", self._act_save_as),
            ("toggle-find", self._act_toggle_find),
            ("zoom-in", lambda *_: self._adjust_font(1)),
            ("zoom-out", lambda *_: self._adjust_font(-1)),
            ("zoom-reset", lambda *_: self._set_font(11)),
            ("about", self._act_about),
        ]
        for name, cb in actions:
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", cb)
            self.add_action(act)

        wrap = Gio.SimpleAction.new_stateful(
            "toggle-wrap", None, GLib.Variant.new_boolean(True)
        )
        wrap.connect("change-state", self._act_toggle_wrap)
        self.add_action(wrap)

    @property
    def active_tab(self) -> EditorTab | None:
        page = self._tab_view.get_selected_page()
        if page is None:
            return None
        child = page.get_child()
        return child if isinstance(child, EditorTab) else None

    def open_tab(self, path: Path | None) -> EditorTab:
        tab = EditorTab(path=path)
        page = self._tab_view.append(tab)
        page.set_title(tab.title)
        tab.connect("meta-changed", lambda t, p=page: (p.set_title(t.title), self._sync_status()))
        self._tab_view.set_selected_page(page)
        tab.text_view.grab_focus()
        self._sync_status()
        return tab

    def _sync_status(self) -> None:
        tab = self.active_tab
        if tab is None:
            return
        line, col, words = tab.get_cursor_stats()
        self.set_title(f"{tab.title} — {APP_NAME}")
        self._status_left.set_text(str(tab.path) if tab.path else "Unsaved Buffer")
        self._status_right.set_text(
            f"Ln {line}, Col {col}  •  {words} words  •  {tab.language}  •  UTF-8"
        )

    def _show_toast(self, msg: str) -> None:
        self._toast_overlay.add_toast(Adw.Toast.new(msg))

    def _on_close_page(self, _tv: Adw.TabView, page: Adw.TabPage) -> bool:
        tab = page.get_child()
        if isinstance(tab, EditorTab) and tab.modified:
            dlg = Adw.AlertDialog.new(
                f"Discard unsaved changes to “{tab.path.name if tab.path else 'Untitled'}”?",
                "Your unsaved edits will be lost.",
            )
            dlg.add_response("cancel", "Cancel")
            dlg.add_response("discard", "Discard")
            dlg.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dlg.set_default_response("cancel")

            def _resp(_d: Adw.AlertDialog, resp: str) -> None:
                confirm = resp == "discard"
                self._tab_view.close_page_finish(page, confirm)
                if confirm and self._tab_view.get_n_pages() == 0:
                    self.close()

            dlg.connect("response", _resp)
            dlg.present(self)
            return True

        self._tab_view.close_page_finish(page, True)
        if self._tab_view.get_n_pages() == 0:
            self.close()
        return True

    def _act_close_tab(self, *_args: object) -> None:
        page = self._tab_view.get_selected_page()
        if page is not None:
            self._tab_view.close_page(page)

    def _act_open(self, *_args: object) -> None:
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Open File")

        def _done(dlg: Gtk.FileDialog, res: Gio.AsyncResult) -> None:
            try:
                gfile = dlg.open_finish(res)
                if gfile and gfile.get_path():
                    self.open_tab(Path(gfile.get_path()))
            except GLib.Error:
                pass

        dialog.open(self, None, _done)

    def _act_save(self, *_args: object) -> None:
        tab = self.active_tab
        if tab is None:
            return
        if tab.path is None:
            self._act_save_as()
            return
        try:
            tab.save_to(tab.path)
            self._show_toast(f"Saved {tab.path.name}")
        except OSError as exc:
            self._show_toast(f"Save failed: {exc}")

    def _act_save_as(self, *_args: object) -> None:
        tab = self.active_tab
        if tab is None:
            return
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Save File As")
        if tab.path is not None:
            dialog.set_initial_name(tab.path.name)
        else:
            dialog.set_initial_name("untitled.txt")

        def _done(dlg: Gtk.FileDialog, res: Gio.AsyncResult) -> None:
            try:
                gfile = dlg.save_finish(res)
                if gfile and gfile.get_path():
                    target = Path(gfile.get_path())
                    tab.save_to(target)
                    self._show_toast(f"Saved {target.name}")
            except GLib.Error:
                pass

        dialog.save(self, None, _done)

    def _act_toggle_find(self, *_args: object) -> None:
        showing = not self._find_revealer.get_reveal_child()
        self._find_revealer.set_reveal_child(showing)
        if showing:
            self._find_entry.grab_focus()

    def _find_next(self) -> bool:
        tab = self.active_tab
        query = self._find_entry.get_text()
        if tab is None or not query:
            return False
        buf = tab.buffer
        cursor = buf.get_iter_at_mark(buf.get_insert())
        found = cursor.forward_search(query, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        if found is None:
            found = buf.get_start_iter().forward_search(
                query, Gtk.TextSearchFlags.CASE_INSENSITIVE, None
            )
        if found is None:
            self._show_toast("No matches found")
            return False
        match_start, match_end = found
        buf.select_range(match_end, match_start)
        tab.text_view.scroll_to_iter(match_start, 0.2, False, 0.0, 0.0)
        return True

    def _replace_one(self) -> None:
        tab = self.active_tab
        if tab is None:
            return
        buf = tab.buffer
        bounds = buf.get_selection_bounds()
        query = self._find_entry.get_text()
        if bounds and buf.get_text(bounds[0], bounds[1], False).casefold() == query.casefold():
            buf.delete(bounds[0], bounds[1])
            buf.insert_at_cursor(self._replace_entry.get_text())
        self._find_next()

    def _replace_all(self) -> None:
        tab = self.active_tab
        query = self._find_entry.get_text()
        if tab is None or not query:
            return
        buf = tab.buffer
        start, end = buf.get_bounds()
        text = buf.get_text(start, end, True)
        replacement = self._replace_entry.get_text()
        count = text.count(query)
        if count == 0:
            self._show_toast("No matches found")
            return
        buf.set_text(text.replace(query, replacement))
        self._show_toast(f"Replaced {count} occurrence{'s' if count != 1 else ''}")

    def _act_toggle_wrap(self, action: Gio.SimpleAction, value: GLib.Variant) -> None:
        enabled = value.get_boolean()
        action.set_state(value)
        for idx in range(self._tab_view.get_n_pages()):
            tab = self._tab_view.get_nth_page(idx).get_child()
            if isinstance(tab, EditorTab):
                tab.set_word_wrap(enabled)

    def _adjust_font(self, delta: int) -> None:
        self._set_font(max(8, min(28, self._font_size + delta)))

    def _set_font(self, size: int) -> None:
        self._font_size = size
        self._apply_font_size()

    def _apply_font_size(self) -> None:
        self._font_provider.load_from_string(
            f".orbit-editor-view {{ font-size: {self._font_size}pt; }}"
        )

    def _act_about(self, *_args: object) -> None:
        about = Adw.AboutDialog()
        about.set_application_name(APP_NAME)
        about.set_version(__version__)
        about.set_application_icon("accessories-text-editor")
        about.set_comments("A lightweight GTK 4 + Libadwaita text & code editor in Python.")
        about.present(self)


class OrbitEditApp(Adw.Application):
    """Orbit Edit application."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.add_main_option(
            "new-window",
            ord("n"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Open a new Orbit Edit window",
            None,
        )

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        load_css_string(EDIT_CSS)
        shortcuts = {
            "win.new-tab": ["<Control>t", "<Control>n"],
            "win.close-tab": ["<Control>w"],
            "win.open": ["<Control>o"],
            "win.save": ["<Control>s"],
            "win.save-as": ["<Control><Shift>s"],
            "win.toggle-find": ["<Control>f", "<Control>h"],
            "win.toggle-wrap": ["<Alt>z"],
            "win.zoom-in": ["<Control>plus", "<Control>equal"],
            "win.zoom-out": ["<Control>minus"],
            "win.zoom-reset": ["<Control>0"],
        }
        for name, accels in shortcuts.items():
            self.set_accels_for_action(name, accels)

    def do_activate(self) -> None:
        win = self.get_active_window()
        if win is None:
            win = OrbitEditWindow(self)
        win.present()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        options = command_line.get_options_dict().end().unpack()
        new_window = bool(options.get("new-window", False))
        args = command_line.get_arguments()[1:]

        paths: list[Path] = []
        for raw in args:
            if not raw or raw.startswith("-"):
                continue
            if raw.startswith("file://"):
                gfile = Gio.File.new_for_uri(raw)
                if gfile.get_path():
                    paths.append(Path(gfile.get_path()))
            else:
                p = Path(raw).expanduser()
                if not p.is_absolute() and command_line.get_cwd():
                    p = Path(command_line.get_cwd()) / p
                paths.append(p)

        active = self.get_active_window()
        if new_window or active is None or not isinstance(active, OrbitEditWindow):
            win = OrbitEditWindow(self, initial_files=paths)
            win.present()
        else:
            if paths:
                for p in paths:
                    active.open_tab(p)
            active.present()
        return 0


def main(argv: list[str] | None = None) -> int:
    app = OrbitEditApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
