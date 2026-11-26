# Orbit OS ISO (`archiso`)

Custom Arch Linux live & installable ISO featuring **ONLY Orbit Desktop (Hyprland)** and **Orbit Desktop (Qtile)** — no COSMIC, GNOME, or KDE bloat.

## Included Out of the Box
- **Display Manager:** SDDM with two clean Wayland sessions:
  - **Orbit Desktop (Hyprland)** (native Lua config + Python GTK 4 **Orbit Shell** top & bottom bars)
  - **Orbit Desktop (Qtile)** (100% Python Wayland WM)
- **Orbit Suite v1.0.0** (system-wide in `/opt/orbit` + `/usr/local/bin/orbit-*`):
  - `orbit-files` (GTK 4 + Libadwaita file manager with thumbnails, tabs, split view, preview pane)
  - `orbit-term` (with native `vte4` preinstalled)
  - `orbit-view` (image viewer)
  - `orbit-launch` (fuzzy launcher + calculator + command runner)
  - `orbit-shell` (GTK 4 + `gtk4-layer-shell` top bar & bottom bar with auto-detecting laptop battery pill)
  - `orbit-nvim` (isolated LazyVim `NVIM_APPNAME=nvim-hyprland`)
- **Laptop Ready:** NetworkManager, PipeWire + WirePlumber, BlueZ, `brightnessctl`, `hyprpolkitagent`, `Papirus-Dark`, `JetBrainsMono Nerd Font`, `fish`, `kitty`, and `archinstall`.

## Build the ISO

```bash
./build-iso.sh
```

The resulting `.iso` will be placed in `./out/` and can be flashed directly to a USB drive with `dd` or Ventoy:

```bash
sudo dd bs=4M if=out/orbit-os-*.iso of=/dev/sdX status=progress oflag=sync
```
