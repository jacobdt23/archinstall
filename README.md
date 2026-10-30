# Jacob's Custom Arch Linux (`CUSTOM_ARCH`)

A custom Arch Linux live ISO (`mkarchiso`) with the **Calamares Graphical Installer**, booting directly into **Jacob's Custom Hyprland + Quickshell (TokyoNight) Desktop** with full **UEFI/BIOS (GPT & MBR)**, **NVIDIA/AMD/Intel**, and **Virtual Machine** support.

---

## Hardware, Boot, Btrfs Rollback & VM Compatibility

* **Boot Modes**: Hybrid ISO (`bios.syslinux` + `uefi.grub`) and Calamares graphical partitioning supporting **UEFI + GPT**, **Legacy BIOS + GPT** (`bios_grub`), and **Legacy BIOS + MBR (`msdos`)**.
* **Bulletproof Btrfs + Timeshift + GRUB-Btrfs + `timeshift-autosnap` Stack**:
  * **Default Btrfs Layout**: Calamares defaults to **Btrfs** (`noatime,compress=zstd:1`) with automatic `@` (`/`), `@home` (`/home`), `@cache` (`/var/cache`), `@log` (`/var/log`), and `@swap` subvolumes.
  * **Timeshift (`timeshift`)**: Pre-configured automatically in **BTRFS mode** on the target disk (`calamares-post-install`) with `cronie.service` enabled for scheduled boot/daily/weekly snapshots.
  * **Automatic Pre-Upgrade Snapshots (`timeshift-autosnap`)**: Pacman hook (`00-timeshift-autosnap.hook`) automatically takes a Btrfs snapshot before any `pacman -Syu` upgrade and regenerates GRUB snapshot entries.
  * **Bootable GRUB Snapshots (`grub-btrfs`)**: `grub-btrfsd.service` is pre-configured with `--syslog --timeshift-auto` (`inotify-tools`) to watch Timeshift snapshots in real time and add them directly to the GRUB boot menu for instant rollback.
* **CPUs**: Bundled with both `amd-ucode` and `intel-ucode`.
* **GPUs & Virtual Machines**:
  * **NVIDIA**: `nvidia-open`, `nvidia-utils`, `nvidia-settings`, `libva-nvidia-driver`, `egl-wayland`, and `nvidia_drm modeset=1 fbdev=1`.
  * **AMD**: `mesa`, `vulkan-radeon`, `xf86-video-amdgpu`, `xf86-video-ati`.
  * **Intel**: `mesa`, `vulkan-intel`, `intel-media-driver`, `libva-intel-driver`, `xf86-video-intel`.
  * **Virtual Machines**: [`/usr/local/bin/Hyprland`](iso/configs/archiso-profile/airootfs/usr/local/bin/Hyprland) automatically detects VMs via `systemd-detect-virt --vm` and enables software rendering fallback (`WLR_RENDERER_ALLOW_SOFTWARE=1`) and software cursors (`WLR_NO_HARDWARE_CURSORS=1`), while keeping native hardware acceleration on bare-metal GPUs.
  * **Runtime Driver Detection**: [`modules/env.lua`](iso/configs/archiso-profile/airootfs/etc/skel/.config/hypr/modules/env.lua) dynamically inspects `lsmod` for `nvidia`, `amdgpu`/`radeon`, or `i915`/`xe` and exports the matching VAAPI/GLX/GBM environment variables.

---

## Repository Structure

* **[`iso/`](iso/)**: Custom Arch Linux live ISO configuration, local Calamares package repo, and build pipeline.
  * **[`iso/configs/archiso-profile/`](iso/configs/archiso-profile/)**:
    * **[`airootfs/etc/calamares/`](iso/configs/archiso-profile/airootfs/etc/calamares/)**: Complete **Calamares Graphical Installer** configuration (`settings.conf`, `custom_arch` branding, and modules for `partition`, `mount`, `unpackfs`, `users`, `displaymanager`, `services-systemd`, `shellprocess`, `initcpiocfg`, `initcpio`, `grubcfg`, `bootloader`).
    * **[`airootfs/etc/skel/.config/`](iso/configs/archiso-profile/airootfs/etc/skel/.config/)**: Bundled dotfiles for **Hyprland** (`hyprland.lua` + Lua modules), **Quickshell** (TopBar, BottomDock with live Calamares `"⬇ Install"` button, Launcher, ControlCenter, Clipboard, Media, Notifications, Calendar, Keybinds, PowerMenu), **Alacritty**, **Hyprlock**, **Hyprpaper**, and **Waypaper**.
    * **[`packages.x86_64`](iso/configs/archiso-profile/packages.x86_64)**: Complete live & desktop package manifest (`calamares`, `kpmcore`, `hyprland`, `quickshell`, `awww`, `pipewire`, `thunar`, `firefox`, etc.).
    * **[`profiledef.sh`](iso/configs/archiso-profile/profiledef.sh)**: ISO profile metadata (`jacob-archlinux`, label `CUSTOM_ARCH`).
  * **[`iso/custom-repo/`](iso/custom-repo/)**: Prebuilt `calamares` (`3.4.2-2`) package and local pacman repository database.
  * **[`iso/scripts/build-iso.sh`](iso/scripts/build-iso.sh)**: Stages the desktop configuration and builds the ISO via `mkarchiso` natively (on Arch) or automatically inside a privileged Arch container via `podman`/`docker` (on Fedora or any other Linux host).

---

## Building the Custom ISO

Run the build script from the repository root (works on **Fedora/other distros** via rootless `podman` or on **Arch Linux** via `sudo`):

```bash
./iso/scripts/build-iso.sh
```

The compiled bootable ISO (`jacob-archlinux-YYYY.MM.DD-x86_64.iso`) will be placed in `iso/out/`.

---

## Installing via Calamares from the Live ISO

The ISO boots directly into the live **Hyprland + Quickshell** desktop on first boot (`tty1`). You can launch the **Calamares Graphical Installer** in any of three ways:

1. **Click the `"⬇ Install"` button** on the bottom Quickshell dock.
2. **Press `SUPER + SHIFT + I`** (or open the Quickshell App Launcher with `SUPER + SPACE` and select **Install System (Calamares)**).
3. **Run from terminal**:
   ```bash
   launch-calamares
   ```

---

## Default Hyprland & Quickshell Keybindings

| Keybind | Action |
| :--- | :--- |
| `SUPER + W` | Toggle **Welcome Center & Keybinds Cheat Sheet** (Auto-opens on first boot) |
| `SUPER + RETURN` | Open Terminal (`kitty`) |
| `SUPER` / `SUPER + SPACE` | Toggle Quickshell App Launcher |
| `SUPER + SHIFT + I` | Launch **Calamares System Installer** (Live ISO) |
| `SUPER + E` | Open File Manager (`thunar`) |
| `SUPER + C` | Close Active Window |
| `SUPER + I` | Toggle Quickshell Control Center |
| `SUPER + K` | Toggle Keybinds Reference |
| `SUPER + N` | Toggle Notifications Center |
| `SUPER + SHIFT + V` | Toggle Clipboard History (`cliphist`) |
| `SUPER + M` | Toggle Media & Audio Controls (`playerctl` / `wpctl`) |
| `SUPER + L` | Toggle Calendar & Agenda Dropdown |
| `SUPER + Q` | Toggle Power Menu (`hyprlock` / Reboot / Shutdown) |
| `SUPER + = / - / BackSpace` | Volume Up / Down / Mute |
| `SUPER + 1-0` | Switch to Workspaces 1–10 |
| `SUPER + SHIFT + 1-0` | Move Window to Workspaces 1–10 |
