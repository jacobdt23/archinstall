"""Orbit Shell — Native Python + GTK 4 + gtk4-layer-shell Top Bar and Floating Bottom Dock."""

from __future__ import annotations

import ctypes
import datetime
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

import cairo

# Ensure libgtk4-layer-shell is linked before GTK initializes Wayland
try:
    ctypes.CDLL("libgtk4-layer-shell.so")
except OSError:
    pass

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Adw, Gdk, GLib, Gtk, Gtk4LayerShell, Pango

APP_ID = "dev.orbit.Shell"

SHELL_CSS = """
window.orbit-bar-window,
window.orbit-dock-window {
    background-color: transparent;
}

.orbit-top-bar {
    background-color: rgba(33, 34, 44, 0.86);
    border: 1px solid rgba(189, 147, 249, 0.35);
    border-radius: 9px;
    padding: 1px 6px;
}

.orbit-bottom-dock {
    background-color: rgba(33, 34, 44, 0.86);
    border: 1px solid rgba(189, 147, 249, 0.35);
    border-radius: 9px;
    padding: 1px 8px;
}

.orbit-pill,
menubutton.orbit-pill > button {
    background-color: rgba(40, 42, 54, 0.88);
    border: 1px solid rgba(68, 71, 90, 0.9);
    border-radius: 6px;
    padding: 1px 7px;
    min-height: 18px;
    color: #f8f8f2;
    font-size: 10px;
    font-weight: 600;
}

menubutton.orbit-pill,
menubutton.orbit-power-btn {
    padding: 0;
    margin: 0;
    border: none;
    background: transparent;
    min-height: 18px;
}

menubutton.orbit-power-btn > button {
    background-color: rgba(33, 34, 44, 0.92);
    border: 1px solid rgba(255, 85, 85, 0.75);
    border-radius: 6px;
    padding: 1px 6px;
    min-height: 18px;
    min-width: 22px;
    color: #ff5555;
}

.orbit-pill:hover {
    background-color: rgba(68, 71, 90, 0.95);
    border-color: rgba(189, 147, 249, 0.75);
}

menubutton.orbit-clock-pill > button,
.orbit-clock-pill {
    background-color: rgba(139, 233, 253, 0.16);
    border: 1px solid rgba(139, 233, 253, 0.45);
    border-bottom: 3px solid #8be9fd;
    color: #8be9fd;
    font-weight: 800;
}

label.orbit-window-title {
    background-color: rgba(189, 147, 249, 0.14);
    border: 1px solid rgba(189, 147, 249, 0.35);
    border-bottom: 3px solid #bd93f9;
    color: #f8f8f2;
    font-size: 11px;
    font-weight: 600;
}

button.orbit-cpu {
    background-color: rgba(189, 147, 249, 0.18);
    border: 1px solid rgba(189, 147, 249, 0.45);
    border-bottom: 3px solid #bd93f9;
    color: #d6acff;
}

button.orbit-mem {
    background-color: rgba(255, 121, 198, 0.18);
    border: 1px solid rgba(255, 121, 198, 0.45);
    border-bottom: 3px solid #ff79c6;
    color: #ff92df;
}

button.orbit-disk {
    background-color: rgba(255, 184, 108, 0.18);
    border: 1px solid rgba(255, 184, 108, 0.45);
    border-bottom: 3px solid #ffb86c;
    color: #ffb86c;
}

button.orbit-net {
    background-color: rgba(241, 250, 140, 0.16);
    border: 1px solid rgba(241, 250, 140, 0.45);
    border-bottom: 3px solid #f1fa8c;
    color: #f1fa8c;
}

menubutton.orbit-vol > button,
.orbit-vol {
    background-color: rgba(80, 250, 123, 0.18);
    border: 1px solid rgba(80, 250, 123, 0.45);
    border-bottom: 3px solid #50fa7b;
    color: #69ff94;
}

menubutton.orbit-media > button,
.orbit-media {
    background-color: rgba(255, 121, 198, 0.22);
    border: 1px solid rgba(255, 121, 198, 0.55);
    border-bottom: 3px solid #ff79c6;
    color: #ff92df;
}

button.orbit-bat {
    background-color: rgba(80, 250, 123, 0.18);
    border: 1px solid rgba(80, 250, 123, 0.45);
    border-bottom: 3px solid #50fa7b;
    color: #50fa7b;
}

button.orbit-bat-low {
    background-color: rgba(255, 85, 85, 0.25);
    border: 1px solid rgba(255, 85, 85, 0.65);
    border-bottom: 3px solid #ff5555;
    color: #ff6e6e;
}

button.orbit-theme-btn {
    background-color: rgba(139, 233, 253, 0.18);
    border: 1px solid rgba(139, 233, 253, 0.45);
    border-bottom: 3px solid #8be9fd;
    color: #8be9fd;
}

.orbit-ws-btn {
    background-color: rgba(40, 42, 54, 0.85);
    border: 1px solid rgba(68, 71, 90, 0.9);
    border-radius: 6px;
    padding: 1px 7px;
    min-width: 22px;
    min-height: 20px;
    color: #6272a4;
    font-size: 10px;
    font-weight: 800;
}

.orbit-ws-btn.occupied {
    background-color: rgba(139, 233, 253, 0.14);
    color: #8be9fd;
    border-color: rgba(139, 233, 253, 0.45);
    border-bottom: 3px solid #8be9fd;
}

.orbit-ws-btn.active {
    background: linear-gradient(135deg, #bd93f9 0%, #ff79c6 100%);
    border-color: #ff79c6;
    border-bottom: 3px solid #f1fa8c;
    color: #21222c;
    font-weight: 900;
}

.orbit-ws-btn:hover {
    border-color: #bd93f9;
}

.orbit-power-btn {
    background-color: rgba(33, 34, 44, 0.92);
    border: 1px solid rgba(255, 85, 85, 0.75);
    border-radius: 7px;
    padding: 1px 6px;
    min-height: 20px;
    color: #ff5555;
}

.orbit-power-btn:hover {
    background-color: #ff5555;
    color: #21222c;
}

.orbit-dock-btn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 2px 6px;
    min-width: 28px;
    min-height: 28px;
    transition: all 140ms ease;
}

.orbit-dock-btn:hover {
    background-color: rgba(189, 147, 249, 0.22);
    border-color: rgba(189, 147, 249, 0.6);
}

.orbit-dock-btn.running {
    border-bottom: 2px solid rgba(189, 147, 249, 0.6);
}

.orbit-dock-btn.focused {
    background-color: rgba(189, 147, 249, 0.18);
    border-bottom: 2px solid #ff79c6;
}

.orbit-dock-sep {
    background-color: rgba(189, 147, 249, 0.3);
    min-width: 1px;
    margin: 6px 4px;
}
"""

def _bin(name: str) -> str:
    local = Path.home() / ".local" / "bin" / name
    if local.exists():
        return str(local)
    return shutil.which(name) or name


PINNED_APPS = [
    ("Orbit Launch", "launch", _bin("orbit-launch")),
    ("Orbit Term", "utilities-terminal", _bin("orbit-term")),
    ("Orbit Files", "system-file-manager", _bin("orbit-files")),
    ("Orbit Edit (LazyVim)", "nvim", _bin("orbit-nvim")),
    ("Orbit View", "image-x-generic", _bin("orbit-view")),
    ("Brave Browser", "brave-browser", "brave"),
]

CLASS_ICON_MAP = {
    "dev.orbit.files": "system-file-manager",
    "dev.orbit.term": "utilities-terminal",
    "dev.orbit.edit": "nvim",
    "dev.orbit.view": "image-x-generic",
    "dev.orbit.launch": "launch",
    "brave-browser": "brave-browser",
    "kitty": "kitty",
    "antigravity": "antigravity",
    "code": "visual-studio-code",
    "thunar": "thunar",
    "pavucontrol": "multimedia-volume-control",
}


def _spawn(cmd: str) -> None:
    subprocess.Popen(cmd, shell=True, start_new_session=True)


def _hyprctl_json(args: list[str]) -> object:
    try:
        out = subprocess.check_output(["hyprctl", "-j", *args], text=True, timeout=1.5)
        return json.loads(out)
    except Exception:
        return None


def _resolve_icon_name(wm_class: str) -> str:
    low = (wm_class or "").strip().lower()
    if low in CLASS_ICON_MAP:
        return CLASS_ICON_MAP[low]
    if low:
        display = Gdk.Display.get_default()
        if display is not None:
            theme = Gtk.IconTheme.get_for_display(display)
            if theme.has_icon(low):
                return low
            if theme.has_icon(wm_class):
                return wm_class
    return "application-x-executable"


class SystemStats:
    """Lightweight /proc-based system metrics without spawning subprocesses."""

    def __init__(self) -> None:
        self._prev_total = 0
        self._prev_idle = 0

    def cpu_percent(self) -> int:
        try:
            line = Path("/proc/stat").read_text().splitlines()[0]
            parts = [int(x) for x in line.split()[1:8]]
            idle = parts[3] + parts[4]
            total = sum(parts)
            dt = total - self._prev_total
            di = idle - self._prev_idle
            self._prev_total = total
            self._prev_idle = idle
            if dt <= 0:
                return 0
            return max(0, min(100, int(round((dt - di) * 100.0 / dt))))
        except Exception:
            return 0

    def mem_summary(self) -> str:
        try:
            info: dict[str, int] = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                k, v = line.split(":", 1)
                info[k] = int(v.strip().split()[0])
            total_kb = info.get("MemTotal", 1)
            avail_kb = info.get("MemAvailable", 0)
            used_gb = (total_kb - avail_kb) / (1024 * 1024)
            pct = int(round((total_kb - avail_kb) * 100 / total_kb))
            return f"{used_gb:.1f}G ({pct}%)"
        except Exception:
            return "—"

    def disk_summary(self) -> str:
        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            pct = int(round(usage.used * 100 / usage.total))
            return f"{free_gb:.0f}G free ({pct}%)"
        except Exception:
            return "—"

    def volume_state(self) -> tuple[int, bool, str]:
        """Return (percent, muted, display_str)."""
        try:
            out = subprocess.check_output(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                text=True,
                timeout=1.0,
            ).strip()
            muted = "MUTED" in out
            pct = int(round(float(out.split()[1]) * 100))
            label = f"Muted ({pct}%)" if muted else f"{pct}%"
            return pct, muted, label
        except Exception:
            return 0, False, "—"

    def media_summary(self) -> tuple[str | None, str]:
        """Return (short_label, full_title) or (None, '') if nothing playing."""
        try:
            status = subprocess.check_output(
                ["playerctl", "status"], text=True, stderr=subprocess.DEVNULL, timeout=0.6
            ).strip()
            if status not in ("Playing", "Paused"):
                return None, ""
            meta = subprocess.check_output(
                ["playerctl", "metadata", "--format", "{{artist}} - {{title}}"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=0.6,
            ).strip(" -")
            if not meta:
                return None, ""
            icon = "▶" if status == "Playing" else "⏸"
            short = meta if len(meta) <= 28 else meta[:27] + "…"
            return f"{icon} {short}", meta
        except Exception:
            return None, ""

    def network_summary(self) -> str:
        try:
            net_dir = Path("/sys/class/net")
            for iface in sorted(net_dir.iterdir()):
                name = iface.name
                if name == "lo":
                    continue
                state = (iface / "operstate").read_text().strip()
                if state == "up":
                    if (iface / "wireless").is_dir() or name.startswith("wl"):
                        return "Wi-Fi"
                    return "Eth"
            return "Offline"
        except Exception:
            return "—"

    def battery_summary(self) -> tuple[str | None, bool]:
        """Return (label, is_low) or (None, False) on desktop machines without a battery."""
        try:
            ps_dir = Path("/sys/class/power_supply")
            bats = sorted(p for p in ps_dir.iterdir() if p.name.startswith("BAT"))
            if not bats:
                return None, False
            bat = bats[0]
            cap = int((bat / "capacity").read_text().strip())
            status = (bat / "status").read_text().strip()
            prefix = "CHG" if status == "Charging" else "BAT"
            return f"{prefix} {cap}%", (cap <= 20 and status != "Charging")
        except Exception:
            return None, False


class CpuSparkline(Gtk.DrawingArea):
    """Lightweight Cairo rolling CPU sparkline graph (qtile-extras style)."""

    def __init__(self, max_points: int = 20) -> None:
        super().__init__()
        self._points: deque[float] = deque([0.0] * max_points, maxlen=max_points)
        self.set_content_width(42)
        self.set_content_height(16)
        self.set_draw_func(self._draw)

    def push(self, pct: int) -> None:
        self._points.append(max(0.0, min(100.0, float(pct))))
        self.queue_draw()

    def _draw(self, _area: Gtk.DrawingArea, cr: cairo.Context, w: int, h: int) -> None:
        pts = list(self._points)
        if len(pts) < 2:
            return
        step = w / (len(pts) - 1)

        # Fill area under sparkline
        cr.move_to(0, h)
        for i, val in enumerate(pts):
            x = i * step
            y = h - (val / 100.0) * (h - 2) - 1
            cr.line_to(x, y)
        cr.line_to(w, h)
        cr.close_path()
        cr.set_source_rgba(0.74, 0.58, 0.98, 0.28)
        cr.fill()

        # Crisp top stroke
        for i, val in enumerate(pts):
            x = i * step
            y = h - (val / 100.0) * (h - 2) - 1
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.set_source_rgba(0.74, 0.58, 0.98, 0.95)
        cr.set_line_width(1.5)
        cr.stroke()


class TopBarWindow(Gtk.ApplicationWindow):
    """Floating frosted-glass top bar for a single monitor."""

    def __init__(self, app: Gtk.Application, monitor: Gdk.Monitor) -> None:
        super().__init__(application=app)
        self.add_css_class("orbit-bar-window")
        self.set_decorated(False)

        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_namespace(self, "orbit-top-bar")
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_monitor(self, monitor)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, 4)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, 10)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, 10)
        Gtk4LayerShell.auto_exclusive_zone_enable(self)

        bar = Gtk.CenterBox()
        bar.add_css_class("orbit-top-bar")
        self.set_child(bar)

        # Left: Workspaces + Active Window Title (app menu kept on Super key & bottom bar)
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self._ws_buttons: dict[int, Gtk.Button] = {}
        for ws in range(1, 10):
            btn = Gtk.Button.new_with_label(str(ws))
            btn.add_css_class("orbit-ws-btn")
            btn.connect("clicked", lambda _b, w=ws: _spawn(f"hyprctl dispatch workspace {w}"))
            self._ws_buttons[ws] = btn
            self._ws_box.append(btn)
        left.append(self._ws_box)

        self._title_lbl = Gtk.Label(label="Hyprland")
        self._title_lbl.add_css_class("orbit-pill")
        self._title_lbl.add_css_class("orbit-window-title")
        self._title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._title_lbl.set_max_width_chars(38)
        left.append(self._title_lbl)
        bar.set_start_widget(left)

        # Center: Clock + Live MPRIS Media Player Pill
        center = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._clock_btn = Gtk.MenuButton()
        self._clock_btn.add_css_class("orbit-pill")
        self._clock_btn.add_css_class("orbit-clock-pill")
        cal_pop = Gtk.Popover()
        cal_pop.set_child(Gtk.Calendar())
        self._clock_btn.set_popover(cal_pop)
        center.append(self._clock_btn)

        self._media_btn = Gtk.MenuButton()
        self._media_btn.add_css_class("orbit-pill")
        self._media_btn.add_css_class("orbit-media")
        self._media_btn.set_visible(False)
        media_pop = Gtk.Popover()
        mbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        mbox.set_margin_top(10)
        mbox.set_margin_bottom(10)
        mbox.set_margin_start(12)
        mbox.set_margin_end(12)
        self._media_full_lbl = Gtk.Label(label="")
        self._media_full_lbl.set_max_width_chars(36)
        self._media_full_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._media_full_lbl.add_css_class("heading")
        mbox.append(self._media_full_lbl)
        mctrls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mctrls.set_halign(Gtk.Align.CENTER)
        for icon_name, cmd in (
            ("media-skip-backward-symbolic", "playerctl previous"),
            ("media-playback-start-symbolic", "playerctl play-pause"),
            ("media-skip-forward-symbolic", "playerctl next"),
        ):
            mb = Gtk.Button.new_from_icon_name(icon_name)
            mb.add_css_class("circular")
            mb.connect("clicked", lambda _b, c=cmd: _spawn(c))
            mctrls.append(mb)
        mbox.append(mctrls)
        media_pop.set_child(mbox)
        self._media_btn.set_popover(media_pop)
        center.append(self._media_btn)

        bar.set_center_widget(center)

        # Right: CPU + Sparkline, RAM, Disk, Net, Battery, Volume Slider Popover, Theme, Power
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self._cpu_btn = Gtk.Button.new_with_label("CPU 0%")
        self._cpu_btn.add_css_class("orbit-pill")
        self._cpu_btn.add_css_class("orbit-cpu")
        self._cpu_btn.set_tooltip_text("CPU Usage (click for btop)")
        self._cpu_btn.connect("clicked", lambda *_: _spawn("kitty -e btop"))
        right.append(self._cpu_btn)

        self._mem_btn = Gtk.Button.new_with_label("RAM —")
        self._mem_btn.add_css_class("orbit-pill")
        self._mem_btn.add_css_class("orbit-mem")
        self._mem_btn.connect("clicked", lambda *_: _spawn("kitty -e btop"))
        right.append(self._mem_btn)

        self._disk_btn = Gtk.Button.new_with_label("Disk —")
        self._disk_btn.add_css_class("orbit-pill")
        self._disk_btn.add_css_class("orbit-disk")
        self._disk_btn.connect("clicked", lambda *_: _spawn(f"{_bin('orbit-files')} /"))
        right.append(self._disk_btn)

        self._net_btn = Gtk.Button.new_with_label("Net —")
        self._net_btn.add_css_class("orbit-pill")
        self._net_btn.add_css_class("orbit-net")
        self._net_btn.set_tooltip_text("Network Settings")
        self._net_btn.connect("clicked", lambda *_: _spawn("nm-connection-editor"))
        right.append(self._net_btn)

        self._bat_btn = Gtk.Button.new_with_label("")
        self._bat_btn.add_css_class("orbit-pill")
        self._bat_btn.add_css_class("orbit-bat")
        self._bat_btn.set_visible(False)
        right.append(self._bat_btn)

        # Interactive Volume Pill + Slider Popover
        self._vol_suppress = False
        self._vol_btn = Gtk.MenuButton()
        self._vol_btn.set_label("Vol —")
        self._vol_btn.add_css_class("orbit-pill")
        self._vol_btn.add_css_class("orbit-vol")
        self._vol_btn.set_tooltip_text("Click: Volume Slider  •  Scroll: Volume")
        vol_pop = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_size_request(210, -1)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        self._vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 150, 5)
        self._vol_scale.set_draw_value(True)
        self._vol_scale.connect("value-changed", self._on_vol_scale_changed)
        vbox.append(self._vol_scale)
        vrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mute_b = Gtk.Button.new_with_label("Mute Toggle")
        mute_b.set_hexpand(True)
        mute_b.connect("clicked", lambda *_: _spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"))
        mixer_b = Gtk.Button.new_with_label("Mixer")
        mixer_b.connect("clicked", lambda *_: (vol_pop.popdown(), _spawn("pavucontrol")))
        vrow.append(mute_b)
        vrow.append(mixer_b)
        vbox.append(vrow)
        vol_pop.set_child(vbox)
        self._vol_btn.set_popover(vol_pop)

        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.connect(
            "scroll",
            lambda _c, _dx, dy: (
                _spawn(
                    "wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+"
                    if dy < 0
                    else "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"
                ),
                True,
            )[1],
        )
        self._vol_btn.add_controller(scroll)
        right.append(self._vol_btn)

        # 1-click Orbit Theme / Wallpaper switcher
        theme_btn = Gtk.Button()
        theme_btn.add_css_class("orbit-pill")
        theme_btn.add_css_class("orbit-theme-btn")
        theme_btn.set_tooltip_text("Orbit Theme & Wallpapers")
        theme_icon = Gtk.Image.new_from_icon_name("preferences-desktop-wallpaper-symbolic")
        theme_icon.set_pixel_size(14)
        theme_btn.set_child(theme_icon)
        theme_btn.connect("clicked", lambda *_: _spawn(_bin("orbit-theme")))
        right.append(theme_btn)

        power_btn = Gtk.MenuButton()
        power_btn.add_css_class("orbit-power-btn")
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown-symbolic")
        power_icon.set_pixel_size(15)
        power_btn.set_child(power_icon)
        power_pop = Gtk.Popover()
        pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pbox.set_margin_top(6)
        pbox.set_margin_bottom(6)
        pbox.set_margin_start(6)
        pbox.set_margin_end(6)
        for lbl, cmd in (
            ("Reload Hyprland", "hyprctl reload"),
            ("Lock Screen", "hyprlock"),
            ("Log Out", "hyprctl dispatch exit"),
            ("Reboot", "systemctl reboot"),
            ("Shut Down", "systemctl poweroff"),
        ):
            b = Gtk.Button.new_with_label(lbl)
            b.add_css_class("flat")
            b.connect("clicked", lambda _b, c=cmd, p=power_pop: (p.popdown(), _spawn(c)))
            pbox.append(b)
        power_pop.set_child(pbox)
        power_btn.set_popover(power_pop)
        right.append(power_btn)

        bar.set_end_widget(right)

    def _on_vol_scale_changed(self, scale: Gtk.Scale) -> None:
        if self._vol_suppress:
            return
        pct = int(round(scale.get_value()))
        _spawn(f"wpctl set-volume @DEFAULT_AUDIO_SINK@ {pct}%")

    def update_clock(self, text: str) -> None:
        self._clock_btn.set_label(text)

    def update_stats(
        self,
        cpu: int,
        mem: str,
        disk: str,
        vol_pct: int,
        vol_label: str,
        net: str,
        bat: str | None,
        bat_low: bool,
        media_short: str | None,
        media_full: str,
    ) -> None:
        self._cpu_btn.set_label(f"CPU {cpu}%")
        self._mem_btn.set_label(f"RAM {mem}")
        self._disk_btn.set_label(f"Disk {disk}")
        self._net_btn.set_label(net)
        self._vol_btn.set_label(f"Vol {vol_label}")
        self._vol_suppress = True
        self._vol_scale.set_value(vol_pct)
        self._vol_suppress = False
        if media_short:
            self._media_btn.set_label(media_short)
            self._media_full_lbl.set_text(media_full)
            self._media_btn.set_visible(True)
        else:
            self._media_btn.set_visible(False)
        if bat is not None:
            self._bat_btn.set_label(bat)
            self._bat_btn.set_visible(True)
            if bat_low:
                self._bat_btn.add_css_class("orbit-bat-low")
            else:
                self._bat_btn.remove_css_class("orbit-bat-low")
        else:
            self._bat_btn.set_visible(False)

    def update_hypr(self, active_ws: int, occupied: set[int], title: str) -> None:
        for ws, btn in self._ws_buttons.items():
            btn.remove_css_class("active")
            btn.remove_css_class("occupied")
            if ws == active_ws:
                btn.add_css_class("active")
            elif ws in occupied:
                btn.add_css_class("occupied")
            # Show workspaces 1..5 always, plus any occupied/active 6..9
            btn.set_visible(ws <= 5 or ws == active_ws or ws in occupied)
        self._title_lbl.set_text(title or "Hyprland")


class BottomDockWindow(Gtk.ApplicationWindow):
    """Full-width slim frosted-glass bottom bar with real app icons + live running taskbar."""

    def __init__(self, app: Gtk.Application, monitor: Gdk.Monitor) -> None:
        super().__init__(application=app)
        self.add_css_class("orbit-dock-window")
        self.set_decorated(False)

        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_namespace(self, "orbit-bottom-dock")
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_monitor(self, monitor)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, 4)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, 10)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, 10)
        Gtk4LayerShell.auto_exclusive_zone_enable(self)

        bar = Gtk.CenterBox()
        bar.add_css_class("orbit-bottom-dock")
        self.set_child(bar)

        # Left: Apps + Search trigger
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_btn = Gtk.Button.new_with_label("Search apps…")
        search_btn.add_css_class("orbit-pill")
        search_btn.set_tooltip_text("Orbit Launch (Super+D)")
        search_btn.connect("clicked", lambda *_: _spawn(_bin("orbit-launch")))
        left.append(search_btn)
        bar.set_start_widget(left)

        # Center: Pinned Orbit apps + running window icons
        center = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        for label, icon_name, cmd in PINNED_APPS:
            btn = Gtk.Button()
            btn.add_css_class("orbit-dock-btn")
            btn.set_tooltip_text(label)
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.set_pixel_size(20)
            btn.set_child(img)
            btn.connect("clicked", lambda _b, c=cmd: _spawn(c))
            center.append(btn)

        self._sep = Gtk.Box()
        self._sep.add_css_class("orbit-dock-sep")
        self._sep.set_visible(False)
        center.append(self._sep)

        self._running_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        center.append(self._running_box)
        bar.set_center_widget(center)

        # Right: Show Desktop / Empty Workspace button
        desk_btn = Gtk.Button.new_with_label("Desktop")
        desk_btn.add_css_class("orbit-pill")
        desk_btn.set_tooltip_text("Switch to Empty Workspace")
        desk_btn.connect("clicked", lambda *_: _spawn("hyprctl dispatch workspace empty"))
        bar.set_end_widget(desk_btn)

    def update_clients(self, clients: list[dict[str, object]], active_addr: str) -> None:
        while (child := self._running_box.get_first_child()) is not None:
            self._running_box.remove(child)

        visible_clients = [
            c for c in clients
            if c.get("mapped") and c.get("class") and c.get("class") != "dev.orbit.Shell"
        ]
        self._sep.set_visible(bool(visible_clients))

        for client in visible_clients:
            addr = str(client.get("address", ""))
            wm_class = str(client.get("class", ""))
            title = str(client.get("title", wm_class))

            btn = Gtk.Button()
            btn.add_css_class("orbit-dock-btn")
            btn.add_css_class("running")
            if addr == active_addr:
                btn.add_css_class("focused")
            btn.set_tooltip_text(title)

            img = Gtk.Image.new_from_icon_name(_resolve_icon_name(wm_class))
            img.set_pixel_size(20)
            btn.set_child(img)

            btn.connect("clicked", lambda _b, a=addr: _spawn(f"hyprctl dispatch focuswindow address:{a}"))
            mid = Gtk.GestureClick()
            mid.set_button(2)
            mid.connect("pressed", lambda *_args, a=addr: _spawn(f"hyprctl dispatch closewindow address:{a}"))
            btn.add_controller(mid)

            self._running_box.append(btn)


class OrbitShellApp(Adw.Application):
    """Manages Orbit Top Bars and Bottom Docks across all connected monitors."""

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self._bars: list[TopBarWindow] = []
        self._docks: list[BottomDockWindow] = []
        self._stats = SystemStats()
        self._hypr_refresh_pending = False

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        dynamic_path = Path.home() / ".config" / "orbit" / "theme.css"
        dynamic_css = dynamic_path.read_text(encoding="utf-8") if dynamic_path.is_file() else ""
        provider = Gtk.CssProvider()
        provider.load_from_string(SHELL_CSS + "\n" + dynamic_css)
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER,
            )

    def do_activate(self) -> None:
        if self._bars:
            return
        display = Gdk.Display.get_default()
        if display is None:
            return

        self._monitors = display.get_monitors()
        self._monitors.connect("items-changed", lambda *_: self._rebuild_monitor_windows())
        self._rebuild_monitor_windows()

        GLib.timeout_add_seconds(1, self._tick_clock)
        GLib.timeout_add_seconds(2, self._tick_stats)
        self._start_hypr_socket_listener()

    def _rebuild_monitor_windows(self) -> None:
        for w in self._bars + self._docks:
            w.close()
        self._bars.clear()
        self._docks.clear()

        for i in range(self._monitors.get_n_items()):
            mon = self._monitors.get_item(i)
            if isinstance(mon, Gdk.Monitor):
                bar = TopBarWindow(self, mon)
                bar.present()
                self._bars.append(bar)

                dock = BottomDockWindow(self, mon)
                dock.present()
                self._docks.append(dock)

        self._tick_clock()
        self._tick_stats()
        self._refresh_hypr()

    def _tick_clock(self) -> bool:
        now = datetime.datetime.now().strftime("%a, %b %d  •  %I:%M %p")
        for bar in self._bars:
            bar.update_clock(now)
        return True

    def _tick_stats(self) -> bool:
        cpu = self._stats.cpu_percent()
        mem = self._stats.mem_summary()
        disk = self._stats.disk_summary()
        vol_pct, _muted, vol_label = self._stats.volume_state()
        net = self._stats.network_summary()
        bat, bat_low = self._stats.battery_summary()
        media_short, media_full = self._stats.media_summary()
        for bar in self._bars:
            bar.update_stats(
                cpu, mem, disk, vol_pct, vol_label, net, bat, bat_low, media_short, media_full
            )
        return True

    def _schedule_hypr_refresh(self) -> None:
        if self._hypr_refresh_pending:
            return
        self._hypr_refresh_pending = True
        GLib.timeout_add(60, self._refresh_hypr)

    def _refresh_hypr(self) -> bool:
        self._hypr_refresh_pending = False
        active_ws_data = _hyprctl_json(["activeworkspace"])
        ws_list = _hyprctl_json(["workspaces"])
        active_win = _hyprctl_json(["activewindow"])
        clients = _hyprctl_json(["clients"])

        active_ws = active_ws_data.get("id", 1) if isinstance(active_ws_data, dict) else 1
        occupied = {
            w.get("id", 0)
            for w in (ws_list if isinstance(ws_list, list) else [])
            if isinstance(w, dict) and w.get("windows", 0) > 0
        }
        title = active_win.get("title", "") if isinstance(active_win, dict) else ""
        active_addr = active_win.get("address", "") if isinstance(active_win, dict) else ""
        client_list = clients if isinstance(clients, list) else []

        for bar in self._bars:
            bar.update_hypr(active_ws, occupied, title)
        for dock in self._docks:
            dock.update_clients(client_list, active_addr)
        return False

    def _start_hypr_socket_listener(self) -> None:
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        if not sig:
            return
        sock_path = Path(runtime) / "hypr" / sig / ".socket2.sock"
        if not sock_path.exists():
            return

        def _worker() -> None:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.connect(str(sock_path))
                    buf = ""
                    while True:
                        chunk = s.recv(4096)
                        if not chunk:
                            break
                        buf += chunk.decode("utf-8", errors="ignore")
                        if "\n" in buf:
                            buf = buf.rsplit("\n", 1)[-1]
                            GLib.idle_add(self._schedule_hypr_refresh)
            except OSError:
                pass

        threading.Thread(target=_worker, daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    app = OrbitShellApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
