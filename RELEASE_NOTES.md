# JacobOS v1.0.0 Release

Welcome to the official **JacobOS v1.0.0** release — a customized Arch Linux rolling distribution featuring Hyprland, a native Python/GTK3 desktop shell, TokyoNight styling, and graphical Calamares installation.

---

### Highlights & Key Features

* **Calamares Graphical Installer (`3.4.2`)**:
  * Complete custom TokyoNight-styled installer.
  * Defaults to **Btrfs** with automatic `@` (`/`), `@home` (`/home`), `@cache` (`/var/cache`), `@log` (`/var/log`), and `@swap` subvolumes.
  * Supports UEFI + GPT, BIOS + GPT, and BIOS + MBR.

* **Bulletproof Rollback Stack**:
  * **Timeshift**: Pre-configured in BTRFS mode with automatic daily, weekly, and boot snapshots via `cronie`.
  * **`timeshift-autosnap`**: Libalpm hook automatically creates a system snapshot before any `pacman -Syu` upgrade.
  * **`grub-btrfs`**: Background daemon (`grub-btrfsd --timeshift-auto`) populates your GRUB boot menu in real time with bootable snapshots for instant recovery.

* **Pure Python/GTK3 Desktop Shell (`jacob-shell`)**:
  * 100% native Python + GTK3 (`gtk-layer-shell`) — zero QML or Quickshell bloat.
  * Top Bar with workspace switcher, date/calendar button, system monitor pills (CPU, RAM, Disk), and volume indicator.
  * Floating Bottom Dock with official full-color application icons.
  * Integrated notification daemon (`org.freedesktop.Notifications`) and clipboard history manager (`cliphist`).
  * Welcome Hub (`SUPER + W`) with essential apps launcher and keybindings cheat sheet.

* **System Control Center (`jacob-control-center`)**:
  * Dedicated settings manager accessible via `SUPER + I` or the dock.
  * Tabs for Audio/Mic (PipeWire), Network/Wi-Fi (NetworkManager), Bluetooth (BlueZ), Hyprland display tuning, Btrfs snapshots, and system maintenance (`pacman`, `reflector`, cache cleanup).

* **Complete Hardware Auto-Detection & VM Ready**:
  * Complete GPU driver stack: NVIDIA (`nvidia-open`, `nvidia-utils`, `nvidia-settings`, `linux-firmware-nvidia`), AMD (`vulkan-radeon`, `linux-firmware-amd`, `linux-firmware-amdgpu`), and Intel (`vulkan-intel`, `intel-media-driver`, `libva-intel-driver`, `linux-firmware-intel`).
  * Dual CPU microcode (`amd-ucode`, `intel-ucode`) dynamically selected at boot.
  * Complete Wi-Fi and Bluetooth chipset firmware (`broadcom`, `realtek`, `intel`, `atheros`, `mediatek`, `cirrus`).
  * Automatic VM detection (`systemd-detect-virt`) enabling software cursor and rendering fallbacks under QEMU, VirtualBox, VMware, and Hyper-V.

* **Preloaded Developer & Terminal Suite**:
  * Complete `base-devel` build environment (`gcc`, `make`, `patch`, etc.).
  * Fast terminals: `kitty` and `alacritty`.
  * Editors: `vim`, `nano`, and `micro`.

---

### Verification & Checksum

* **ISO Image**: `jacob-archlinux-2026.10.30-x86_64.iso` (2.10 GB / 2,105,573,376 bytes)
* **SHA-256 Checksum**:
  ```
  e78b8400d5d21071cc94e479e8bfcdd1edef616a7004a28d13e02ee0d1547951  jacob-archlinux-2026.10.30-x86_64.iso
  ```
* **Verify**:
  ```bash
  sha256sum -c jacob-archlinux-2026.10.30-x86_64.iso.sha256
  ```
