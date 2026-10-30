# Jacob's Custom Arch Linux Installer

This directory contains both the full-disk UEFI/BIOS (GPT & MBR) installer (`install.sh`) and modular post-installation scripts (`scripts/`).

## 1. Full-Disk UEFI/BIOS (GPT & MBR) Installation (`install.sh`)

When booted into an Arch Linux live ISO (or via `archinstall-custom` on the custom ISO):

```bash
sudo ./installer/install.sh
```

### Features
- **Boot & Partitioning Modes**:
  1. **UEFI + GPT** (512MiB FAT32 ESP, 4GiB Swap, ext4 Root)
  2. **Legacy BIOS + GPT** (2MiB `bios_grub`, 4GiB Swap, ext4 Root)
  3. **Legacy BIOS + MBR / `msdos`** (4GiB Swap, bootable ext4 Root)
- **Hardware Support**:
  - Installs `amd-ucode` and `intel-ucode`.
  - Supports installing **All GPU Vendors (NVIDIA + AMD + Intel)** or selecting NVIDIA-only, AMD-only, or Intel-only.
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
