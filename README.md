# Jacob's Custom Arch Linux (`CUSTOM_ARCH`)

A unified custom Arch Linux live ISO builder (`mkarchiso`) and interactive **UEFI/BIOS (GPT & MBR)** system installer pre-configured with **Jacob's Custom Hyprland + Quickshell (TokyoNight) + XFCE Fallback Desktop** and full **NVIDIA, AMD, and Intel** CPU & GPU support.

---

## Hardware & Boot Compatibility

* **Boot Modes**: Hybrid ISO (`bios.syslinux` + `uefi.grub`) and installer supporting **UEFI + GPT**, **Legacy BIOS + GPT** (`bios_grub`), and **Legacy BIOS + MBR (`msdos`)**.
* **CPUs**: Bundled with both `amd-ucode` and `intel-ucode`.
* **GPUs**:
  * **NVIDIA**: `nvidia-open`, `nvidia-utils`, `nvidia-settings`, `libva-nvidia-driver`, `egl-wayland`, and `nvidia_drm modeset=1 fbdev=1`.
  * **AMD**: `mesa`, `vulkan-radeon`, `xf86-video-amdgpu`, `xf86-video-ati`.
  * **Intel**: `mesa`, `vulkan-intel`, `intel-media-driver`, `libva-intel-driver`, `xf86-video-intel`.
  * **Auto-Detection**: [`modules/env.lua`](iso/configs/archiso-profile/airootfs/etc/skel/.config/hypr/modules/env.lua) automatically detects which GPU driver (`nvidia`, `amdgpu`/`radeon`, or `i915`/`xe`) is loaded at runtime and sets the matching VAAPI/GLX/GBM environment variables.

---

## Repository Structure

* **[`iso/`](iso/)**: Custom UEFI-compatible Arch Linux live ISO configuration and build scripts.
  * **[`iso/configs/archiso-profile/`](iso/configs/archiso-profile/)**:
    * **[`airootfs/etc/skel/.config/`](iso/configs/archiso-profile/airootfs/etc/skel/.config/)**: Bundled dotfiles for **Hyprland** (`hyprland.conf` + Lua modules), **Quickshell** (TopBar, BottomDock, Launcher, ControlCenter, Clipboard, Media, Notifications, Calendar, Keybinds, PowerMenu), **Alacritty**, **Hyprlock**, **Hyprpaper**, and **Waypaper**.
    * **[`packages.x86_64`](iso/configs/archiso-profile/packages.x86_64)**: Complete live & desktop package manifest (`hyprland`, `quickshell`, `awww`, `pipewire`, `xfce4`, `arch-install-scripts`, `mkinitcpio-archiso`, etc.).
    * **[`profiledef.sh`](iso/configs/archiso-profile/profiledef.sh)**: ISO profile metadata (`jacob-archlinux`, label `CUSTOM_ARCH`).
  * **[`iso/scripts/build-iso.sh`](iso/scripts/build-iso.sh)**: Automatically stages `installer/` and dotfiles into the live ISO and builds via `mkarchiso` natively (on Arch) or automatically inside a privileged Arch container via `podman`/`docker` (on Fedora or any other Linux host).
* **[`installer/`](installer/)**: Full-disk UEFI/GPT system installer and modular post-install scripts.
  * **[`installer/install.sh`](installer/install.sh)**: Interactive full-disk UEFI/GPT installer (`archinstall-custom` inside the live ISO) that partitions, installs Arch, configures GRUB, and deploys your custom Hyprland + Quickshell desktop and dotfiles.
  * **[`installer/scripts/install.sh`](installer/scripts/install.sh)**: Interactive post-install/modular menu for adding desktop environments, packages, users, and dotfiles on an existing Arch system.

---

## Building the Custom ISO

Run the build script with `sudo` from the repository root (works on both **Arch Linux** via `mkarchiso` and **Fedora/other distros** via `podman`/`docker`):

```bash
sudo ./iso/scripts/build-iso.sh
```

The compiled bootable ISO (`jacob-archlinux-YYYY.MM.DD-x86_64.iso`) will be placed in `iso/out/`.

---

## Installing from the Live ISO

Once booted into the live environment:

1. **Run the unified installer** (available directly in `$PATH`):
   ```bash
   archinstall-custom
   ```
   *(Or run `/root/installer/install.sh` directly.)*
2. **Or test the live Hyprland desktop directly**:
   ```bash
   Hyprland
   ```

---

## Default Hyprland & Quickshell Keybindings

| Keybind | Action |
| :--- | :--- |
| `SUPER + RETURN` | Open Terminal (`kitty`) |
| `SUPER` / `SUPER + SPACE` | Toggle Quickshell App Launcher |
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
