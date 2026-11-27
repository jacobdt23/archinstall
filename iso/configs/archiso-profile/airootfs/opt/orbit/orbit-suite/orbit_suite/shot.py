"""Orbit Shot — A GTK 4 + Libadwaita screenshot utility for Orbit Desktop (Wayland/Hyprland)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

from orbit_suite import __version__  # noqa: E402
from orbit_suite.common import load_css_string  # noqa: E402

APP_ID = "dev.orbit.Shot"
APP_NAME = "Orbit Shot"

SHOT_CSS = """
window.orbit-shot-window {
    background-color: #282a36;
    color: #f8f8f2;
}
.orbit-shot-card {
    background-color: rgba(33, 34, 44, 0.92);
    border: 1px solid rgba(189, 147, 249, 0.35);
    border-radius: 12px;
    padding: 14px;
}
.orbit-shot-mode-btn {
    background-color: rgba(40, 42, 54, 0.95);
    border: 1px solid rgba(68, 71, 90, 0.9);
    border-radius: 10px;
    padding: 12px 10px;
    color: #f8f8f2;
    font-weight: 600;
}
.orbit-shot-mode-btn:hover {
    background-color: rgba(68, 71, 90, 0.95);
    border-color: #bd93f9;
}
.orbit-shot-primary {
    background: linear-gradient(135deg, #bd93f9 0%, #ff79c6 100%);
    color: #21222c;
    font-weight: 800;
    border-radius: 10px;
    padding: 10px 18px;
}
.orbit-shot-preview-frame {
    background-color: #191a21;
    border: 1px solid rgba(68, 71, 90, 0.9);
    border-radius: 10px;
    padding: 8px;
}
.orbit-shot-meta {
    color: #8be9fd;
    font-size: 11px;
    font-weight: 600;
}
"""


def screenshots_dir() -> Path:
    d = Path.home() / "Pictures" / "Screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_output_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return screenshots_dir() / f"orbit-shot-{stamp}.png"


def _hyprctl_json(cmd: str) -> object | None:
    if not shutil.which("hyprctl"):
        return None
    try:
        out = subprocess.check_output(["hyprctl", "-j", cmd], text=True, timeout=2.0)
        return json.loads(out)
    except Exception:
        return None


def _active_monitor_name() -> str | None:
    monitors = _hyprctl_json("monitors")
    if isinstance(monitors, list):
        for m in monitors:
            if isinstance(m, dict) and m.get("focused"):
                return str(m.get("name", "")) or None
    return None


def _active_window_geometry() -> str | None:
    win = _hyprctl_json("activewindow")
    if not isinstance(win, dict):
        return None
    at = win.get("at")
    size = win.get("size")
    if (
        isinstance(at, list)
        and isinstance(size, list)
        and len(at) == 2
        and len(size) == 2
        and size[0] > 0
        and size[1] > 0
    ):
        return f"{int(at[0])},{int(at[1])} {int(size[0])}x{int(size[1])}"
    return None


def copy_image_to_clipboard(path: Path) -> bool:
    wl_copy = shutil.which("wl-copy")
    if not wl_copy or not path.is_file():
        return False
    try:
        data = path.read_bytes()
        proc = subprocess.Popen(
            [wl_copy, "--type", "image/png"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert proc.stdin is not None
        proc.stdin.write(data)
        proc.stdin.close()
        return True
    except Exception:
        return False


def send_notification(title: str, body: str, icon_path: Path | None = None) -> None:
    notify = shutil.which("notify-send")
    if not notify:
        return
    cmd = [notify, "-a", APP_NAME]
    if icon_path and icon_path.is_file():
        cmd.extend(["-i", str(icon_path)])
    cmd.extend([title, body])
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def capture_screenshot(
    mode: str,
    delay: int = 0,
    copy_clip: bool = True,
    save_file: bool = True,
    annotate: bool = False,
) -> tuple[Path | None, str | None]:
    """Capture a screenshot using grim/slurp. Returns (path, error_message)."""
    grim = shutil.which("grim")
    if not grim:
        return None, "grim is not installed."

    geom: str | None = None
    output_mon: str | None = None

    if mode == "region":
        slurp = shutil.which("slurp")
        if not slurp:
            return None, "slurp is not installed."
        res = subprocess.run(
            [slurp, "-b", "#282a3666", "-c", "#bd93f9ff", "-w", "2"],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0 or not res.stdout.strip():
            return None, "cancelled"
        geom = res.stdout.strip()
    elif mode == "window":
        geom = _active_window_geometry()
        if not geom:
            return None, "No focused Hyprland window found."
    elif mode == "monitor":
        output_mon = _active_monitor_name()
        if not output_mon:
            return None, "Could not detect focused monitor."
    elif mode != "full":
        return None, f"Unknown capture mode: {mode}"

    if delay > 0:
        time.sleep(delay)

    target = default_output_path() if save_file else Path(f"/tmp/orbit-shot-{int(time.time())}.png")
    cmd = [grim]
    if geom:
        cmd.extend(["-g", geom])
    elif output_mon:
        cmd.extend(["-o", output_mon])
    cmd.append(str(target))

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not target.is_file():
        return None, res.stderr.strip() or "grim failed to capture screenshot."

    if copy_clip:
        copy_image_to_clipboard(target)

    if annotate and shutil.which("swappy"):
        subprocess.Popen(
            ["swappy", "-f", str(target), "-o", str(target)],
            start_new_session=True,
        )

    return target, None


class OrbitShotWindow(Adw.ApplicationWindow):
    """Interactive Orbit Shot capture & preview window."""

    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.add_css_class("orbit-shot-window")
        self.set_default_size(640, 480)
        self._last_path: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Image.new_from_icon_name("applets-screenshooter")
        icon.set_pixel_size(18)
        title_box.append(icon)
        lbl = Gtk.Label(label=APP_NAME)
        lbl.add_css_class("title")
        title_box.append(lbl)
        header.set_title_widget(title_box)

        folder_btn = Gtk.Button.new_from_icon_name("folder-open-symbolic")
        folder_btn.set_tooltip_text("Open Screenshots Folder")
        folder_btn.connect("clicked", lambda *_: self._open_folder())
        header.pack_start(folder_btn)
        toolbar.add_top_bar(header)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        toolbar.set_content(self._stack)

        # --- Page 1: Capture Controls ---
        capture_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        capture_page.set_margin_top(18)
        capture_page.set_margin_bottom(18)
        capture_page.set_margin_start(18)
        capture_page.set_margin_end(18)

        modes_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        modes_card.add_css_class("orbit-shot-card")

        heading = Gtk.Label(label="Choose Capture Mode", xalign=0)
        heading.add_css_class("heading")
        modes_card.append(heading)

        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_column_homogeneous(True)

        modes = [
            ("region", "Select Region", "edit-select-all-symbolic", "Drag to select an area (slurp)"),
            ("window", "Active Window", "window-maximize-symbolic", "Capture the focused window"),
            ("monitor", "Active Monitor", "video-display-symbolic", "Capture the focused screen"),
            ("full", "All Monitors", "view-fullscreen-symbolic", "Capture entire desktop"),
        ]
        for idx, (mode_key, label, icon_name, tip) in enumerate(modes):
            btn = Gtk.Button()
            btn.add_css_class("orbit-shot-mode-btn")
            btn.set_tooltip_text(tip)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_halign(Gtk.Align.CENTER)
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.set_pixel_size(28)
            box.append(img)
            box.append(Gtk.Label(label=label))
            btn.set_child(box)
            btn.connect("clicked", lambda _b, m=mode_key: self._start_capture(m))
            grid.attach(btn, idx % 2, idx // 2, 1, 1)

        modes_card.append(grid)
        capture_page.append(modes_card)

        opts_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        opts_card.add_css_class("orbit-shot-card")

        delay_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        delay_row.append(Gtk.Label(label="Capture Delay:", xalign=0, hexpand=True))
        self._delay_dd = Gtk.DropDown.new_from_strings(["0 seconds", "3 seconds", "5 seconds", "10 seconds"])
        delay_row.append(self._delay_dd)
        opts_card.append(delay_row)

        self._copy_chk = Gtk.CheckButton(label="Copy to clipboard automatically")
        self._copy_chk.set_active(True)
        opts_card.append(self._copy_chk)

        self._save_chk = Gtk.CheckButton(label=f"Save to {screenshots_dir()}")
        self._save_chk.set_active(True)
        opts_card.append(self._save_chk)

        capture_page.append(opts_card)

        self._status_lbl = Gtk.Label(label="Shortcuts: Print = GUI • Super+Shift+S = Region • Shift+Print = Monitor", xalign=0.5)
        self._status_lbl.add_css_class("orbit-shot-meta")
        capture_page.append(self._status_lbl)

        self._stack.add_named(capture_page, "capture")

        # --- Page 2: Preview & Actions ---
        preview_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        preview_page.set_margin_top(14)
        preview_page.set_margin_bottom(14)
        preview_page.set_margin_start(14)
        preview_page.set_margin_end(14)

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add_css_class("orbit-shot-preview-frame")
        frame.set_vexpand(True)
        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_vexpand(True)
        self._picture.set_hexpand(True)
        frame.append(self._picture)
        preview_page.append(frame)

        self._meta_lbl = Gtk.Label(label="", xalign=0)
        self._meta_lbl.add_css_class("orbit-shot-meta")
        self._meta_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        preview_page.append(self._meta_lbl)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.set_halign(Gtk.Align.CENTER)

        copy_btn = Gtk.Button(label="Copy")
        copy_btn.add_css_class("orbit-shot-primary")
        copy_btn.connect("clicked", lambda *_: self._copy_current())
        actions.append(copy_btn)

        if shutil.which("swappy"):
            ann_btn = Gtk.Button(label="Annotate")
            ann_btn.add_css_class("orbit-shot-mode-btn")
            ann_btn.connect("clicked", lambda *_: self._annotate_current())
            actions.append(ann_btn)

        open_btn = Gtk.Button(label="Open Folder")
        open_btn.add_css_class("orbit-shot-mode-btn")
        open_btn.connect("clicked", lambda *_: self._open_folder())
        actions.append(open_btn)

        new_btn = Gtk.Button(label="New Capture")
        new_btn.add_css_class("orbit-shot-mode-btn")
        new_btn.connect("clicked", lambda *_: self._stack.set_visible_child_name("capture"))
        actions.append(new_btn)

        del_btn = Gtk.Button(label="Delete")
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", lambda *_: self._delete_current())
        actions.append(del_btn)

        preview_page.append(actions)
        self._stack.add_named(preview_page, "preview")

    def _selected_delay(self) -> int:
        idx = self._delay_dd.get_selected()
        return [0, 3, 5, 10][idx] if 0 <= idx < 4 else 0

    def _start_capture(self, mode: str) -> None:
        delay = self._selected_delay()
        copy_clip = self._copy_chk.get_active()
        save_file = self._save_chk.get_active()
        self.set_visible(False)

        def _do_capture() -> bool:
            # Small pause so Hyprland unmaps Orbit Shot before grim grabs the frame
            time.sleep(0.22)
            path, err = capture_screenshot(
                mode=mode,
                delay=delay,
                copy_clip=copy_clip,
                save_file=save_file,
                annotate=False,
            )
            self.set_visible(True)
            self.present()
            if err == "cancelled":
                self._status_lbl.set_text("Selection cancelled.")
                return False
            if err or path is None:
                self._status_lbl.set_text(f"Capture failed: {err}")
                return False
            self._show_preview(path, copied=copy_clip)
            return False

        GLib.timeout_add(60, _do_capture)

    def _show_preview(self, path: Path, copied: bool) -> None:
        self._last_path = path
        self._picture.set_file(Gio.File.new_for_path(str(path)))
        dims = ""
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file(str(path))
            dims = f"{pb.get_width()}×{pb.get_height()} • "
        except Exception:
            pass
        clip_note = "Copied to clipboard • " if copied else ""
        self._meta_lbl.set_text(f"{clip_note}{dims}{path}")
        self._stack.set_visible_child_name("preview")

    def _copy_current(self) -> None:
        if self._last_path and copy_image_to_clipboard(self._last_path):
            self._meta_lbl.set_text(f"Copied to clipboard • {self._last_path}")

    def _annotate_current(self) -> None:
        if self._last_path and shutil.which("swappy"):
            subprocess.Popen(
                ["swappy", "-f", str(self._last_path), "-o", str(self._last_path)],
                start_new_session=True,
            )

    def _open_folder(self) -> None:
        fm = shutil.which("orbit-files") or str(Path.home() / ".local" / "bin" / "orbit-files")
        if Path(fm).is_file():
            subprocess.Popen([fm, str(screenshots_dir())], start_new_session=True)
        else:
            subprocess.Popen(["xdg-open", str(screenshots_dir())], start_new_session=True)

    def _delete_current(self) -> None:
        if self._last_path and self._last_path.is_file():
            try:
                self._last_path.unlink()
            except OSError:
                pass
        self._last_path = None
        self._status_lbl.set_text("Screenshot deleted.")
        self._stack.set_visible_child_name("capture")


class OrbitShotApp(Adw.Application):
    """Orbit Shot GTK 4 Application."""

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-application-prefer-dark-theme", True)
            if Path("/usr/share/icons/Papirus-Dark").is_dir():
                settings.set_property("gtk-icon-theme-name", "Papirus-Dark")
        load_css_string(SHOT_CSS)

    def do_activate(self) -> None:
        win = OrbitShotWindow(self)
        win.present()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orbit-shot", description="Orbit Shot — Wayland/Hyprland Screenshot Utility")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--region", "-r", action="store_true", help="Select a screen region interactively")
    group.add_argument("--window", "-w", action="store_true", help="Capture the active Hyprland window")
    group.add_argument("--monitor", "-m", action="store_true", help="Capture the focused monitor")
    group.add_argument("--full", "-f", action="store_true", help="Capture all monitors")
    parser.add_argument("--delay", "-d", type=int, default=0, help="Delay in seconds before capture")
    parser.add_argument("--annotate", "-a", action="store_true", help="Open capture in swappy for annotation")
    parser.add_argument("--no-copy", action="store_true", help="Do not copy image to clipboard")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args, remaining = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    cli_mode = None
    if args.region:
        cli_mode = "region"
    elif args.window:
        cli_mode = "window"
    elif args.monitor:
        cli_mode = "monitor"
    elif args.full:
        cli_mode = "full"

    if cli_mode is not None:
        path, err = capture_screenshot(
            mode=cli_mode,
            delay=max(0, args.delay),
            copy_clip=not args.no_copy,
            save_file=True,
            annotate=args.annotate,
        )
        if err == "cancelled":
            return 0
        if err or path is None:
            print(f"orbit-shot: {err}", file=sys.stderr)
            send_notification("Screenshot Failed", err or "Unknown error")
            return 1
        clip_txt = " (copied to clipboard)" if not args.no_copy else ""
        send_notification("Screenshot Saved", f"{path.name}{clip_txt}", icon_path=path)
        print(str(path))
        return 0

    app = OrbitShotApp()
    return app.run([sys.argv[0], *remaining])


if __name__ == "__main__":
    raise SystemExit(main())
