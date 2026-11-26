"""Orbit Term — A GTK 4 + Libadwaita multi-tab terminal emulator in Python.

Automatically uses native VTE4 (Vte 3.91) when installed for full VT100/xterm/fish/vim
compatibility, and falls back to an interactive Python PTY widget otherwise.
"""

from __future__ import annotations

import fcntl
import os
import pty
import re
import signal
import struct
import subprocess
import sys
import termios
from pathlib import Path

import gi

from orbit_suite import __version__
from orbit_suite.common import load_css_string

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango

try:
    gi.require_version("Vte", "3.91")
    from gi.repository import Vte  # type: ignore[attr-defined]

    HAS_VTE = True
except (ValueError, ImportError):
    Vte = None  # type: ignore[assignment]
    HAS_VTE = False

APP_ID = "dev.orbit.Term"
APP_NAME = "Orbit Term"

TERM_CSS = """
.orbit-term-view {
    background-color: #13161d;
    color: #e6eaf2;
    font-family: monospace;
}
"""

_ANSI_RE = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"        # OSC sequences
    r"|\x1bP[^\x1b]*(?:\x1b\\)"                # DCS sequences (e.g. XTGETTCAP)
    r"|\x1b\[([0-9;?<=>!]*)([A-Za-z])"          # CSI sequences
    r"|\x1b[()#%*+\-./][0-9A-Za-z]"             # Charset / 3-byte ESC sequences
    r"|\x1b[@-Z\\-_=>]"                         # 2-byte ESC sequences (incl. = and >)
)

_SGR_COLORS = {
    30: "#414868", 31: "#f7768e", 32: "#9ece6a", 33: "#e0af68",
    34: "#7aa2f7", 35: "#bb9af7", 36: "#7dcfff", 37: "#c0caf5",
    90: "#565f89", 91: "#ff7a93", 92: "#b9f27c", 93: "#ff9e64",
    94: "#7da6ff", 95: "#bb9af7", 96: "#0db9d7", 97: "#ffffff",
}

_PALETTE_HEX = [
    "#15161e", "#f7768e", "#9ece6a", "#e0af68",
    "#7aa2f7", "#bb9af7", "#7dcfff", "#a9b1d6",
    "#414868", "#ff7a93", "#b9f27c", "#ff9e64",
    "#7da6ff", "#c099ff", "#0db9d7", "#c0caf5",
]


def _rgba(hex_color: str) -> Gdk.RGBA:
    c = Gdk.RGBA()
    c.parse(hex_color)
    return c


class VteTerminalTab(Gtk.ScrolledWindow):
    """Native VTE4-backed terminal tab (full xterm-256color, fish, vim, htop support)."""

    __gsignals__ = {
        "exited": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "title-changed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, cwd: str | None = None, font_size: int = 11) -> None:
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.term = Vte.Terminal()
        self.term.set_scrollback_lines(10000)
        self.term.set_scroll_on_output(False)
        self.term.set_scroll_on_keystroke(True)
        self.term.set_bold_is_bright(True)
        self.term.set_colors(
            _rgba("#c0caf5"),
            _rgba("#13161d"),
            [_rgba(h) for h in _PALETTE_HEX],
        )
        self.set_font_size(font_size)

        self.term.connect("child-exited", lambda *_: self.emit("exited"))
        self.term.connect(
            "window-title-changed",
            lambda t: self.emit("title-changed", t.get_window_title() or "Shell"),
        )

        self.set_child(self.term)

        shell = os.environ.get("SHELL", "/bin/bash")
        self.term.spawn_async(
            Vte.PtyFlags.DEFAULT,
            cwd or str(Path.home()),
            [shell],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            None,
        )

    def focus_terminal(self) -> None:
        self.term.grab_focus()

    def set_font_size(self, size: int) -> None:
        desc = Pango.FontDescription.from_string(f"Monospace {size}")
        self.term.set_font(desc)

    def copy_selection(self) -> None:
        self.term.copy_clipboard_format(Vte.Format.TEXT)

    def paste_clipboard(self) -> None:
        self.term.paste_clipboard()

    def clear_screen(self) -> None:
        self.term.reset(True, True)

    def cleanup(self) -> None:
        pass


class PtyTerminalTab(Gtk.ScrolledWindow):
    """Fallback interactive PTY-backed terminal tab with ANSI/truecolor support."""

    __gsignals__ = {
        "exited": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "title-changed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, cwd: str | None = None, font_size: int = 11) -> None:
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self._cwd = cwd or str(Path.home())
        self._master_fd: int | None = None
        self._watch_id: int | None = None
        self._proc: subprocess.Popen[bytes] | None = None
        self._current_fg: str | None = None
        self._bold: bool = False
        self._cr_pending: bool = False

        self.buffer = Gtk.TextBuffer()
        self._tags: dict[tuple[str | None, bool], Gtk.TextTag] = {}

        self.text_view = Gtk.TextView.new_with_buffer(self.buffer)
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(True)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        self.text_view.set_left_margin(10)
        self.text_view.set_right_margin(10)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)
        self.text_view.add_css_class("orbit-term-view")

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.text_view.add_controller(key_ctrl)

        self.set_child(self.text_view)
        self._spawn_shell()

    def focus_terminal(self) -> None:
        self.text_view.grab_focus()

    def set_font_size(self, _size: int) -> None:
        # Handled via window-level CSS provider for the fallback TextView
        pass

    def _spawn_shell(self) -> None:
        master_fd, slave_fd = pty.openpty()
        # Set a sensible initial PTY window size (32 rows x 110 cols)
        try:
            winsize = struct.pack("HHHH", 32, 110, 0, 0)
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass
        os.set_blocking(master_fd, False)
        self._master_fd = master_fd

        shell = os.environ.get("SHELL", "/bin/bash")
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        def _setup_controlling_tty() -> None:
            os.setsid()
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        self._proc = subprocess.Popen(
            [shell, "-i"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self._cwd,
            env=env,
            preexec_fn=_setup_controlling_tty,
            close_fds=True,
        )
        os.close(slave_fd)

        self._watch_id = GLib.io_add_watch(
            master_fd,
            GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
            self._on_pty_readable,
        )

    def write_bytes(self, data: bytes) -> None:
        if self._master_fd is not None:
            try:
                os.write(self._master_fd, data)
            except OSError:
                pass

    def clear_screen(self) -> None:
        self.buffer.set_text("")

    def copy_selection(self) -> None:
        bounds = self.buffer.get_selection_bounds()
        if not bounds:
            return
        text = self.buffer.get_text(bounds[0], bounds[1], False)
        display = Gdk.Display.get_default()
        if display is not None:
            display.get_clipboard().set(text)

    def paste_clipboard(self) -> None:
        display = Gdk.Display.get_default()
        if display is None:
            return
        clipboard = display.get_clipboard()

        def _done(cb: Gdk.Clipboard, res: Gio.AsyncResult) -> None:
            try:
                text = cb.read_text_finish(res)
                if text:
                    self.write_bytes(text.encode("utf-8"))
            except GLib.Error:
                pass

        clipboard.read_text_async(None, _done)

    def _get_tag(self) -> Gtk.TextTag | None:
        if self._current_fg is None and not self._bold:
            return None
        key = (self._current_fg, self._bold)
        tag = self._tags.get(key)
        if tag is None:
            props: dict[str, object] = {}
            if self._current_fg is not None:
                props["foreground"] = self._current_fg
            if self._bold:
                props["weight"] = 700
            tag = self.buffer.create_tag(None, **props)
            self._tags[key] = tag
        return tag

    def _erase_current_line(self) -> None:
        end = self.buffer.get_end_iter()
        line_start = end.copy()
        line_start.set_line_offset(0)
        self.buffer.delete(line_start, end)

    def _insert_chunk(self, text: str) -> None:
        if not text:
            return
        tag = self._get_tag()
        for ch in text:
            if ch == "\r":
                self._cr_pending = True
                continue
            if ch == "\n":
                self._cr_pending = False
            elif self._cr_pending:
                self._cr_pending = False
                self._erase_current_line()

            if ch == "\x08":
                end = self.buffer.get_end_iter()
                if end.get_line_offset() > 0:
                    prev = end.copy()
                    prev.backward_char()
                    self.buffer.delete(prev, end)
                continue
            if ch == "\x07":
                continue

            end = self.buffer.get_end_iter()
            if tag is not None:
                self.buffer.insert_with_tags(end, ch, tag)
            else:
                self.buffer.insert(end, ch)

    def _handle_sgr(self, params: str) -> None:
        codes = [int(p) for p in params.split(";") if p.isdigit()] if params else [0]
        idx = 0
        while idx < len(codes):
            code = codes[idx]
            if code == 0:
                self._current_fg = None
                self._bold = False
            elif code == 1:
                self._bold = True
            elif code == 22:
                self._bold = False
            elif code == 39:
                self._current_fg = None
            elif code in _SGR_COLORS:
                self._current_fg = _SGR_COLORS[code]
            elif code == 38 and idx + 4 < len(codes) and codes[idx + 1] == 2:
                r, g, b = codes[idx + 2], codes[idx + 3], codes[idx + 4]
                self._current_fg = f"#{r:02x}{g:02x}{b:02x}"
                idx += 4
            elif code == 38 and idx + 2 < len(codes) and codes[idx + 1] == 5:
                n = codes[idx + 2]
                if 0 <= n < 16:
                    self._current_fg = _PALETTE_HEX[n]
                idx += 2
            idx += 1

    def _append_ansi_text(self, raw: str) -> None:
        pos = 0
        for match in _ANSI_RE.finditer(raw):
            if match.start() > pos:
                self._insert_chunk(raw[pos : match.start()])
            params, cmd = match.group(1), match.group(2)
            if cmd == "m":
                if not (params and params.startswith((">", "?", "<"))):
                    self._handle_sgr(params or "")
            elif cmd == "c" and (params in (None, "", "0")):
                # Respond to Primary Device Attributes (DA1) so fish starts instantly
                self.write_bytes(b"\x1b[?62;c")
            elif cmd == "n" and params == "6":
                # Respond to Cursor Position Report (CPR)
                self.write_bytes(b"\x1b[1;1R")
            elif cmd == "J" and params in ("2", "3"):
                self.buffer.set_text("")
            elif cmd == "K" and params in ("", "0", "2"):
                if self._cr_pending or params == "2":
                    self._cr_pending = False
                    self._erase_current_line()
            pos = match.end()
        if pos < len(raw):
            self._insert_chunk(raw[pos:])

        if self.buffer.get_line_count() > 4000:
            s = self.buffer.get_start_iter()
            cut = self.buffer.get_iter_at_line(self.buffer.get_line_count() - 3000)
            self.buffer.delete(s, cut)

        end_mark = self.buffer.get_insert()
        self.buffer.place_cursor(self.buffer.get_end_iter())
        self.text_view.scroll_to_mark(end_mark, 0.0, False, 0.0, 1.0)

    def _on_pty_readable(self, fd: int, condition: GLib.IOCondition) -> bool:
        if condition & GLib.IOCondition.IN:
            try:
                data = os.read(fd, 8192)
                if not data:
                    self.emit("exited")
                    return False
                self._append_ansi_text(data.decode("utf-8", errors="replace"))
            except OSError:
                self.emit("exited")
                return False
        if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
            self.emit("exited")
            return False
        return True

    def _on_key_pressed(
        self,
        _ctrl: Gtk.EventControllerKey,
        keyval: int,
        _keycode: int,
        state: Gdk.ModifierType,
    ) -> bool:
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if ctrl and shift:
            return False

        if ctrl and not shift:
            uni = Gdk.keyval_to_unicode(keyval)
            if uni and 64 <= uni <= 122:
                code = uni & 0x1F
                self.write_bytes(bytes([code]))
                return True

        special = {
            Gdk.KEY_Return: b"\r",
            Gdk.KEY_KP_Enter: b"\r",
            Gdk.KEY_BackSpace: b"\x7f",
            Gdk.KEY_Tab: b"\t",
            Gdk.KEY_Escape: b"\x1b",
            Gdk.KEY_Up: b"\x1b[A",
            Gdk.KEY_Down: b"\x1b[B",
            Gdk.KEY_Right: b"\x1b[C",
            Gdk.KEY_Left: b"\x1b[D",
            Gdk.KEY_Home: b"\x1b[H",
            Gdk.KEY_End: b"\x1b[F",
            Gdk.KEY_Delete: b"\x1b[3~",
        }
        if keyval in special:
            self.write_bytes(special[keyval])
            return True

        uni = Gdk.keyval_to_unicode(keyval)
        if uni:
            self.write_bytes(chr(uni).encode("utf-8"))
            return True
        return False

    def cleanup(self) -> None:
        if self._watch_id is not None:
            GLib.source_remove(self._watch_id)
            self._watch_id = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
        if self._proc is not None and self._proc.poll() is None:
            try:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGHUP)
            except OSError:
                self._proc.terminate()


TerminalTab = VteTerminalTab if HAS_VTE else PtyTerminalTab


class OrbitTermWindow(Adw.ApplicationWindow):
    """Main Orbit Term window."""

    def __init__(self, app: Adw.Application, initial_cwd: str | None = None) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(940, 600)
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
        self.add_tab(initial_cwd)

    def _build_ui(self) -> None:
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header = Adw.HeaderBar()
        new_tab_btn = Gtk.Button.new_from_icon_name("tab-new-symbolic")
        new_tab_btn.set_tooltip_text("New Tab (Ctrl+Shift+T)")
        new_tab_btn.set_action_name("win.new-tab")
        header.pack_start(new_tab_btn)

        menu = Gio.Menu()
        menu.append("Copy", "win.copy")
        menu.append("Paste", "win.paste")
        menu.append("Clear", "win.clear")
        menu.append("Zoom In", "win.zoom-in")
        menu.append("Zoom Out", "win.zoom-out")
        menu.append("Reset Zoom", "win.zoom-reset")
        menu.append("About Orbit Term", "win.about")
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)
        toolbar_view.add_top_bar(header)

        self._tab_view = Adw.TabView()
        self._tab_view.connect("close-page", self._on_close_page)

        self._tab_bar = Adw.TabBar()
        self._tab_bar.set_view(self._tab_view)
        self._tab_bar.set_autohide(True)
        toolbar_view.add_top_bar(self._tab_bar)

        toolbar_view.set_content(self._tab_view)
        self.connect("close-request", self._on_window_close)

    def _setup_actions(self) -> None:
        actions = [
            ("new-tab", lambda *_: self.add_tab(None)),
            ("close-tab", self._act_close_tab),
            ("copy", lambda *_: self.active_tab and self.active_tab.copy_selection()),
            ("paste", lambda *_: self.active_tab and self.active_tab.paste_clipboard()),
            ("clear", lambda *_: self.active_tab and self.active_tab.clear_screen()),
            ("zoom-in", lambda *_: self._set_font(min(26, self._font_size + 1))),
            ("zoom-out", lambda *_: self._set_font(max(8, self._font_size - 1))),
            ("zoom-reset", lambda *_: self._set_font(11)),
            ("about", self._act_about),
        ]
        for name, cb in actions:
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", cb)
            self.add_action(act)

    @property
    def active_tab(self) -> TerminalTab | None:  # type: ignore[valid-type]
        page = self._tab_view.get_selected_page()
        if page is None:
            return None
        return page.get_child()  # type: ignore[return-value]

    def add_tab(self, cwd: str | None = None) -> TerminalTab:  # type: ignore[valid-type]
        tab = TerminalTab(cwd=cwd, font_size=self._font_size)
        page = self._tab_view.append(tab)
        label = Path(cwd).name if cwd else Path(os.environ.get("SHELL", "shell")).name
        page.set_title(label or "Shell")
        tab.connect("exited", lambda _t, p=page: self._tab_view.close_page(p))
        tab.connect("title-changed", lambda _t, title, p=page: p.set_title(title))
        self._tab_view.set_selected_page(page)
        tab.focus_terminal()
        return tab

    def _on_close_page(self, _tv: Adw.TabView, page: Adw.TabPage) -> bool:
        child = page.get_child()
        if hasattr(child, "cleanup"):
            child.cleanup()
        self._tab_view.close_page_finish(page, True)
        if self._tab_view.get_n_pages() == 0:
            self.close()
        return True

    def _on_window_close(self, _win: Gtk.Window) -> bool:
        for idx in range(self._tab_view.get_n_pages()):
            child = self._tab_view.get_nth_page(idx).get_child()
            if hasattr(child, "cleanup"):
                child.cleanup()
        return False

    def _act_close_tab(self, *_args: object) -> None:
        page = self._tab_view.get_selected_page()
        if page is not None:
            self._tab_view.close_page(page)

    def _set_font(self, size: int) -> None:
        self._font_size = size
        self._apply_font_size()
        for idx in range(self._tab_view.get_n_pages()):
            child = self._tab_view.get_nth_page(idx).get_child()
            if hasattr(child, "set_font_size"):
                child.set_font_size(size)

    def _apply_font_size(self) -> None:
        self._font_provider.load_from_string(
            f".orbit-term-view {{ font-size: {self._font_size}pt; }}"
        )

    def _act_about(self, *_args: object) -> None:
        backend = "VTE 4 (native)" if HAS_VTE else "Python PTY fallback"
        about = Adw.AboutDialog()
        about.set_application_name(APP_NAME)
        about.set_version(__version__)
        about.set_application_icon("utilities-terminal")
        about.set_comments(f"A multi-tab GTK 4 + Libadwaita terminal emulator ({backend}).")
        about.present(self)


class OrbitTermApp(Adw.Application):
    """Orbit Term application."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        load_css_string(TERM_CSS)
        shortcuts = {
            "win.new-tab": ["<Control><Shift>t"],
            "win.close-tab": ["<Control><Shift>w"],
            "win.copy": ["<Control><Shift>c"],
            "win.paste": ["<Control><Shift>v"],
            "win.clear": ["<Control><Shift>k"],
            "win.zoom-in": ["<Control>plus", "<Control>equal"],
            "win.zoom-out": ["<Control>minus"],
            "win.zoom-reset": ["<Control>0"],
        }
        for name, accels in shortcuts.items():
            self.set_accels_for_action(name, accels)

    def do_activate(self) -> None:
        win = OrbitTermWindow(self)
        win.present()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        args = [a for a in command_line.get_arguments()[1:] if a and not a.startswith("-")]
        cwd = args[0] if args and Path(args[0]).is_dir() else command_line.get_cwd()
        win = OrbitTermWindow(self, initial_cwd=cwd)
        win.present()
        return 0


def main(argv: list[str] | None = None) -> int:
    app = OrbitTermApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
