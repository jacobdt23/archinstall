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
from pathlib import Path

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
    background-color: rgba(20, 22, 34, 0.80);
    border: 1px solid rgba(122, 162, 247, 0.30);
    border-radius: 10px;
    padding: 2px 6px;
}

.orbit-bottom-dock {
    background-color: rgba(20, 22, 34, 0.82);
    border: 1px solid rgba(122, 162, 247, 0.32);
    border-radius: 10px;
    padding: 2px 8px;
}

.orbit-pill {
    background-color: rgba(26, 27, 38, 0.78);
    border: 1px solid rgba(41, 46, 66, 0.85);
    border-radius: 7px;
    padding: 1px 8px;
    min-height: 20px;
    color: #c0caf5;
    font-size: 10px;
    font-weight: 600;
}

.orbit-pill:hover {
    background-color: rgba(36, 40, 59, 0.95);
    border-color: rgba(122, 162, 247, 0.65);
}

.orbit-clock-pill {
    border-color: rgba(122, 162, 247, 0.38);
    color: #7dcfff;
    font-weight: 700;
}

.orbit-window-title {
    color: #7dcfff;
    font-size: 11px;
    font-weight: 500;
}

.orbit-cpu { color: #7aa2f7; }
.orbit-mem { color: #bb9af7; }
.orbit-disk { color: #e0af68; }
.orbit-vol { color: #9ece6a; }
.orbit-net { color: #7dcfff; }
.orbit-bat { color: #9ece6a; }
.orbit-bat-low { color: #f7768e; }

.orbit-ws-btn {
    background-color: rgba(26, 27, 38, 0.72);
    border: 1px solid rgba(41, 46, 66, 0.85);
    border-radius: 6px;
    padding: 1px 6px;
    min-width: 20px;
    min-height: 20px;
    color: #565f89;
    font-size: 10px;
    font-weight: 700;
}

.orbit-ws-btn.occupied {
    color: #c0caf5;
    border-color: rgba(122, 162, 247, 0.35);
}

.orbit-ws-btn.active {
    background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
    border-color: #7aa2f7;
    color: #14161f;
    font-weight: 900;
}

.orbit-ws-btn:hover {
    border-color: #7aa2f7;
}

.orbit-power-btn {
    background-color: rgba(20, 22, 31, 0.9);
    border: 1px solid rgba(247, 118, 142, 0.75);
    border-radius: 7px;
    padding: 1px 6px;
    min-height: 20px;
    color: #f7768e;
}

.orbit-power-btn:hover {
    background-color: #f7768e;
    color: #14161f;
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
    background-color: rgba(122, 162, 247, 0.20);
    border-color: rgba(122, 162, 247, 0.55);
}

.orbit-dock-btn.running {
    border-bottom: 2px solid rgba(122, 162, 247, 0.55);
}

.orbit-dock-btn.focused {
    background-color: rgba(122, 162, 247, 0.16);
    border-bottom: 2px solid #7aa2f7;
}

.orbit-dock-sep {
    background-color: rgba(122, 162, 247, 0.25);
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

    def volume_summary(self) -> str:
        try:
            out = subprocess.check_output(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                text=True,
                timeout=1.0,
            ).strip()
            muted = "MUTED" in out
            val = float(out.split()[1])
            pct = int(round(val * 100))
            return f"Muted ({pct}%)" if muted else f"{pct}%"
        except Exception:
            return "—"

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

        # Left: Launcher + Workspaces + Active Window Title
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        brand_btn = Gtk.Button()
        brand_btn.add_css_class("orbit-pill")
        brand_btn.set_tooltip_text("Orbit Launch (Super+D)")
        brand_icon = Gtk.Image.new_from_icon_name("distributor-logo-archlinux")
        brand_icon.set_pixel_size(18)
        brand_btn.set_child(brand_icon)
        brand_btn.connect("clicked", lambda *_: _spawn(_bin("orbit-launch")))
        left.append(brand_btn)

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

        # Center: Clock with Calendar Popover
        self._clock_btn = Gtk.MenuButton()
        self._clock_btn.add_css_class("orbit-pill")
        self._clock_btn.add_css_class("orbit-clock-pill")
        cal_pop = Gtk.Popover()
        cal_pop.set_child(Gtk.Calendar())
        self._clock_btn.set_popover(cal_pop)
        bar.set_center_widget(self._clock_btn)

        # Right: CPU, RAM, Disk, Volume, Power menu
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self._cpu_btn = Gtk.Button.new_with_label("CPU 0%")
        self._cpu_btn.add_css_class("orbit-pill")
        self._cpu_btn.add_css_class("orbit-cpu")
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

        self._vol_btn = Gtk.Button.new_with_label("Vol —")
        self._vol_btn.add_css_class("orbit-pill")
        self._vol_btn.add_css_class("orbit-vol")
        self._vol_btn.set_tooltip_text("Scroll: Volume  •  Click: Mute  •  Right-click: Mixer")
        self._vol_btn.connect("clicked", lambda *_: _spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"))
        rc = Gtk.GestureClick()
        rc.set_button(3)
        rc.connect("pressed", lambda *_: _spawn("pavucontrol"))
        self._vol_btn.add_controller(rc)
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

    def update_clock(self, text: str) -> None:
        self._clock_btn.set_label(text)

    def update_stats(
        self, cpu: int, mem: str, disk: str, vol: str, net: str, bat: str | None, bat_low: bool
    ) -> None:
        self._cpu_btn.set_label(f"CPU {cpu}%")
        self._mem_btn.set_label(f"RAM {mem}")
        self._disk_btn.set_label(f"Disk {disk}")
        self._net_btn.set_label(net)
        self._vol_btn.set_label(f"Vol {vol}")
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
        provider = Gtk.CssProvider()
        provider.load_from_string(SHELL_CSS)
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
        vol = self._stats.volume_summary()
        net = self._stats.network_summary()
        bat, bat_low = self._stats.battery_summary()
        for bar in self._bars:
            bar.update_stats(cpu, mem, disk, vol, net, bat, bat_low)
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
