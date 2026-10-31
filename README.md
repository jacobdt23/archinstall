# JacobOS (`CUSTOM_ARCH`)

A custom Arch Linux rolling distribution and live ISO (`mkarchiso`) featuring the **Calamares Graphical Installer**, booting directly into **JacobOS Hyprland + Python/GTK3 (TokyoNight) Desktop Shell** with full **UEFI/BIOS (GPT & MBR)**, **NVIDIA/AMD/Intel**, and **Virtual Machine** auto-detection.

[![Release](https://img.shields.io/badge/Release-v1.0.0-7aa2f7?style=for-the-badge&logo=archlinux)](https://github.com/jacobdt23/archinstall/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/License-GPLv3-bb9af7?style=for-the-badge)](LICENSE)
[![Desktop](https://img.shields.io/badge/Desktop-Hyprland%20%2B%20Python%2FGTK3-7dcfff?style=for-the-badge)](iso/configs/archiso-profile/airootfs/usr/local/bin/jacob-shell)

---

## Download Latest ISO

The newest build is published automatically by GitHub Actions on every push to `main`:

* **Latest ISO**: [**Latest ISO release**](https://github.com/jacobdt23/archinstall/releases/tag/latest-iso)
* The ISO is slightly over GitHub's 2 GiB per-file limit, so it is split into `jacob-archlinux.iso.part00` and `.part01`.
* **Join the parts** (Windows, Command Prompt):
  ```
  copy /b jacob-archlinux.iso.part00 + jacob-archlinux.iso.part01 jacob-archlinux.iso
  ```
  Linux/macOS: `cat jacob-archlinux.iso.part* > jacob-archlinux.iso`
* **Verify Download**: compare `sha256sum jacob-archlinux.iso` with the hash in `SHA256SUMS`.
* Boot in **UEFI** mode and let the installer format the EFI partition.
* The older [v1.0.0 release](https://github.com/jacobdt23/archinstall/releases/tag/v1.0.0) has known installer bugs.

---

## Hardware Auto-Detection & VM Compatibility

JacobOS automatically detects your hardware and configures the environment on first boot without manual intervention:

* **GPUs**:
  * **NVIDIA**: Automatic detection via [`modules/env.lua`](iso/configs/archiso-profile/airootfs/etc/skel/.config/hypr/modules/env.lua). Loads `nvidia-open`, `nvidia-utils`, `nvidia-settings`, `libva-nvidia-driver`, and sets `LIBVA_DRIVER_NAME=nvidia`, `GBM_BACKEND=nvidia-drm`, `__GLX_VENDOR_LIBRARY_NAME=nvidia`, and `nvidia_drm modeset=1 fbdev=1`.
  * **AMD**: Loads `mesa`, `vulkan-radeon`, `linux-firmware-amd`, `linux-firmware-amdgpu`, and sets `LIBVA_DRIVER_NAME=radeonsi`.
  * **Intel**: Loads `mesa`, `vulkan-intel`, `intel-media-driver` (iHD), `libva-intel-driver` (i965), `linux-firmware-intel`, and sets `LIBVA_DRIVER_NAME=iHD`.
* **Virtual Machines**:
  * [`/usr/local/bin/Hyprland`](iso/configs/archiso-profile/airootfs/usr/local/bin/Hyprland) wrapper runs `systemd-detect-virt --vm`. Under QEMU, VirtualBox, VMware, or Hyper-V, it automatically enables software rendering fallback (`WLR_RENDERER_ALLOW_SOFTWARE=1`) and software cursors (`WLR_NO_HARDWARE_CURSORS=1`), while preserving full hardware acceleration on bare metal.
* **CPUs**: Bundled with dual `amd-ucode` and `intel-ucode` microcode, automatically selected by the bootloader.
* **Wi-Fi & Bluetooth**: Complete client firmware for Intel, Realtek, Broadcom, Qualcomm/Atheros, and MediaTek (MT7922/MT7961 Wi-Fi 6E).
* **Boot Modes**: Hybrid ISO supporting **UEFI + GPT**, **Legacy BIOS + GPT** (`bios_grub`), and **Legacy BIOS + MBR (`msdos`)**.

---

## Bulletproof Btrfs + Timeshift Rollback Stack

* **Default Btrfs Subvolumes**: Calamares partitions the disk with `noatime,compress=zstd:1` and automatically provisions:
  * `@` $\rightarrow$ `/`
  * `@home` $\rightarrow$ `/home`
  * `@cache` $\rightarrow$ `/var/cache`
  * `@log` $\rightarrow$ `/var/log`
  * `@swap` $\rightarrow$ `/swap`
* **Timeshift (`timeshift`)**: Pre-configured in **BTRFS mode** on the target disk via `calamares-post-install` with `cronie.service` enabled for automatic daily, weekly, and boot snapshots.
* **Pre-Upgrade Snapshots (`timeshift-autosnap`)**: Libalpm pacman hook (`00-timeshift-autosnap.hook`) automatically snapshots the root filesystem before any `pacman -Syu` upgrade.
* **Bootable GRUB Snapshots (`grub-btrfs`)**: The `grub-btrfsd.service` daemon (`--timeshift-auto`) monitors snapshots in real time via `inotify-tools` and automatically updates the GRUB boot menu with bootable snapshot entries for one-click rollback.

---

## Desktop Shell & System Control Center

JacobOS features a native desktop stack written entirely in **Python 3 and GTK3** (`gtk-layer-shell`), eliminating all QML/Quickshell dependencies:

1. **`jacob-shell`**:
   * **Top Bar**: Workspace switcher (1–10), live date & calendar dropdown, real-time hardware monitor pills (CPU%, RAM, Disk), volume status, and quick control buttons.
   * **Floating Bottom Dock**: High-resolution application launchers (Kitty, Alacritty, Thunar, Firefox, Pavucontrol, Blueman, Timeshift, Calamares installer).
   * **App Launcher (`SUPER` / `SUPER + SPACE`)**: Instant search and launch for all installed applications.
   * **Welcome Hub (`SUPER + W`)**: Autostarts on first boot. Features an Essential Apps launcher and an interactive Keybindings Reference cheat sheet.
   * **Clipboard Manager (`SUPER + SHIFT + V`)**: Visual clipboard history powered by `cliphist` and `wl-clipboard`.
   * **Notification Daemon**: Internal `org.freedesktop.Notifications` D-Bus server with popups and notification history center.
   * **Media Controls (`SUPER + M`)**: Player controls for `playerctl` and PipeWire audio devices.
   * **Power Menu (`SUPER + Q`)**: Lock (`hyprlock`), Suspend, Reboot, and Shutdown.

2. **`jacob-control-center` (`SUPER + I`)**:
   * **Audio & Mic**: Live PipeWire sink/source volume sliders and mute toggles.
   * **Network & Wi-Fi**: NetworkManager integration (`nmcli`) with SSID discovery, connection status, and one-click scan.
   * **Bluetooth**: BlueZ controller integration (`bluetoothctl`) with scan, paired devices, and connect/disconnect buttons.
   * **Hyprland & Display**: Live sliders for inner/outer gaps, border radius, blur strength, active border colors, and animations toggle.
   * **Btrfs & Snapshots**: Live status of Btrfs subvolumes, Timeshift snapshot listing, and one-click manual snapshot creation.
   * **System & Maintenance**: Live hardware specs (CPU, GPU, RAM, Kernel), one-click `pacman -Syu` system upgrade, Reflector mirror ranking, and pacman cache cleanup.

3. **Preloaded Developer & Terminal Suite**:
   * Full `base-devel` build environment (`gcc`, `binutils`, `make`, `patch`, `fakeroot`, `autoconf`, etc.).
   * Terminals: `kitty` and `alacritty`.
   * Text Editors: `vim`, `nano`, and `micro`.

---

## Repository Structure

```
archinstall/
├── RELEASE_NOTES.md                       # Release notes and checksums
├── README.md                              # Project documentation
└── iso/
    ├── custom-repo/                       # Local Calamares & timeshift-autosnap repo
    │   ├── calamares-3.4.2-2-x86_64.pkg.tar.zst
    │   ├── timeshift-autosnap-0.10.0-1-any.pkg.tar.zst
    │   └── customrepo.db.tar.gz
    ├── configs/
    │   └── archiso-profile/               # Archiso build manifest
    │       ├── packages.x86_64            # Package list (NVIDIA, AMD, Intel, base-devel)
    │       ├── pacman.conf                # Pacman configuration
    │       ├── profiledef.sh              # ISO metadata & compression settings
    │       └── airootfs/                  # Live filesystem overlay
    │           ├── etc/
    │           │   ├── os-release         # JacobOS rolling distribution branding
    │           │   ├── calamares/         # Custom Calamares installer configuration
    │           │   └── skel/.config/      # TokyoNight Hyprland, Kitty, Alacritty dotfiles
    │           └── usr/local/bin/
    │               ├── jacob-shell        # Python/GTK3 desktop shell & dock
    │               ├── jacob-control-center # Python/GTK3 system settings center
    │               ├── Hyprland           # VM-aware Hyprland launch wrapper
    │               └── launch-calamares   # Graphical installer launcher
    └── scripts/
        └── build-iso.sh                   # Native or containerized build script
```

---

## Building the Custom ISO

Run the build script from the repository root (works on **Fedora/Ubuntu/Debian** via rootless `podman` or on **Arch Linux** via `sudo`):

```bash
./iso/scripts/build-iso.sh
```

The compiled bootable ISO (`jacob-archlinux-YYYY.MM.DD-x86_64.iso`) will be placed in `iso/out/`.

---

## Installing via Calamares

The ISO boots directly into the live **Hyprland + Python/GTK** desktop on first boot (`tty1`). You can launch the **Calamares Graphical Installer** in any of three ways:

1. **Click the `"⬇ Install"` button** on the bottom dock.
2. **Press `SUPER + SHIFT + I`** (or open the App Launcher with `SUPER + SPACE` and select **Install System (Calamares)**).
3. **Run from terminal**:
   ```bash
   launch-calamares
   ```

---

## Keybindings Cheat Sheet

| Keybind | Action |
| :--- | :--- |
| `SUPER + W` | Toggle **Welcome Center & Keybinds Cheat Sheet** (Auto-opens on first boot) |
| `SUPER + RETURN` | Open Terminal (`kitty`) |
| `SUPER` / `SUPER + SPACE` | Toggle App Launcher |
| `SUPER + SHIFT + I` | Launch **Calamares System Installer** (Live ISO) |
| `SUPER + E` | Open File Manager (`thunar`) |
| `SUPER + C` | Close Active Window |
| `SUPER + I` | Open System Control Center (`jacob-control-center`) |
| `SUPER + K` | Toggle Keybinds Reference |
| `SUPER + N` | Toggle Notifications Center |
| `SUPER + SHIFT + V` | Toggle Clipboard History (`cliphist`) |
| `SUPER + M` | Toggle Media & Audio Controls (`playerctl` / `wpctl`) |
| `SUPER + L` | Toggle Calendar & Agenda Dropdown |
| `SUPER + Q` | Toggle Power Menu (`hyprlock` / Reboot / Shutdown) |
| `SUPER + = / - / BackSpace` | Volume Up / Down / Mute |
| `SUPER + 1-0` | Switch to Workspaces 1–10 |
| `SUPER + SHIFT + 1-0` | Move Window to Workspaces 1–10 |
