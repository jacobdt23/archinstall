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

* **Bulletproof GRUB + Btrfs Boot Reliability**:
  * Resolved `loader/i386/linux.c:grub_cmd_linux: premature end of file /@/boot/vmlinuz-linux`.
  * Guarantees `/boot` is explicitly uncompressed (`chattr +m`, `btrfs property set compression none`) so GRUB's userspace driver reads raw kernel & initramfs extents without compression bugs.
  * Embedded CPU microcode backup restoring `intel-ucode.img` and `amd-ucode.img` to `/boot`.

---

### Verification & Checksum

* **ISO Image**: `jacob-archlinux-2026.10.30-x86_64.iso` (2.12 GB / 2,120,302,592 bytes)
* **SHA-256 Checksum**:
  ```
  be5ae9fef7ba516abb66630b9a670677e969da1530fc078919e36f8278079289  jacob-archlinux-2026.10.30-x86_64.iso
  ```
* **Verify**:
  ```bash
  sha256sum -c jacob-archlinux-2026.10.30-x86_64.iso.sha256
  ```
