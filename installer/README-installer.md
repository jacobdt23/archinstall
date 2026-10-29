# Jacob's Custom Arch Linux Installer

This directory contains both the full-disk UEFI/GPT installer (`install.sh`) and modular post-installation scripts (`scripts/`).

## 1. Full-Disk UEFI/GPT Installation (`install.sh`)

When booted into an Arch Linux live ISO (or via `archinstall-custom` on the custom ISO):

```bash
sudo ./installer/install.sh
```

### Features
- **Interactive Setup**: Prompts for keyboard layout, timezone, target disk (`/dev/sda`, `/dev/vda`, `/dev/nvme0n1`), hostname, and user credentials.
- **Desktop Profiles**:
  1. **Jacob's Custom Hyprland + Quickshell + XFCE Fallback (Default)** — Installs the complete Hyprland/Quickshell/PipeWire stack and automatically deploys the bundled TokyoNight dotfiles to `/etc/skel/.config` and `/home/<user>/.config`.
  2. **KDE Plasma + Wayland**
  3. **GNOME**
  4. **XFCE**
  5. **Base CLI Only**

## 2. Modular Package & Post-Install Menu (`scripts/install.sh`)

To customize an already-installed Arch Linux system or deploy the custom dotfiles to a user:

```bash
sudo ./installer/scripts/install.sh
```
