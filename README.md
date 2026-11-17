# HyprFrost Linux (`HYPRFROST`)

A custom Arch Linux rolling distribution and live ISO (`mkarchiso`) featuring the **Calamares Graphical Installer** and booting directly via **SDDM (Wayland)** into the **Omarchy** desktop environment (built from [`jacobdt23/omarchy`](https://github.com/jacobdt23/omarchy) branch `jacob-rtx5070`) with **UEFI/BIOS (GPT & MBR)**, **Btrfs + Timeshift + GRUB snapshots**, **Stock Arch Kernel + `nvidia-open`**, and automatic **VM software-rendering fallback**.

[![License](https://img.shields.io/badge/License-GPLv3-bb9af7?style=for-the-badge)](LICENSE)
[![Desktop](https://img.shields.io/badge/Desktop-Omarchy%20(Hyprland%20%2B%20Quickshell)-7dcfff?style=for-the-badge)](https://github.com/jacobdt23/omarchy)

---

## Download Latest ISO

The newest build is published automatically by GitHub Actions on every push to `main`:

* **Latest ISO**: [**Latest ISO release**](https://github.com/jacobdt23/archinstall/releases/tag/latest-iso)
* Download the `.iso` file from that release and write it to a USB stick (Rufus DD mode or Ventoy). If split for the 2 GiB release asset limit, rejoin with `cat jacob-archlinux.iso.part* > jacob-archlinux.iso`.
* **Verify Download**: compare `sha256sum <iso file>` with the hash in `SHA256SUMS`.
* Boot in **UEFI** mode and let the installer format the EFI partition.

---

## Omarchy Desktop & Graphics Stack

* **Omarchy Integration (`jacobdt23/omarchy#jacob-rtx5070`)**:
  * Packaged via `omarchy-keyring`, `omarchy-settings-custom`, and `omarchy-custom` in [`iso/pkgbuilds/`](iso/pkgbuilds/), built cleanly without overriding GRUB, `mkinitcpio`, `Timeshift`, or `/etc/os-release`.
  * Uses `[omarchy]` repo packages (`omarchy/hyprland`, `omarchy/quickshell`, `omarchy-hyprland-titlebars`, `owe`, `omasnap`, `omarchy-screensaver`, `omarchy-power-profiles-daemon`, etc.) ordered after `[core]`, `[extra]`, and `[multilib]` so stock Arch `linux` and `nvidia-open` remain matched.
  * Live session auto-logs into **SDDM Wayland -> Omarchy (Hyprland + uwsm + Quickshell)** with Calamares pinned and auto-started for immediate installation.
* **NVIDIA (`nvidia-open`) & Universal Hardware Support**:
  * Keeps stock Arch `linux` + `nvidia-open`, `nvidia-utils`, `lib32-nvidia-utils`, `nvidia-settings`, and `libva-nvidia-driver` from `[extra]` / `[multilib]`.
  * Ships `/etc/modprobe.d/nvidia.conf` (`nvidia_drm modeset=1 fbdev=1` and `NVreg_PreserveVideoMemoryAllocations=1`), kernel `nvidia-drm.modeset=1`, and auto-detects NVIDIA GPUs during `calamares-post-install` to enable early KMS in `/etc/mkinitcpio.conf.d/nvidia.conf` plus `nvidia-{suspend,resume,hibernate}.service`.
  * Dual `1920x1080@100` defaults plus NVIDIA Wayland safeguards (`no_hardware_cursors = true`, `direct_scanout = 0`) are included in the forked Omarchy config, while Omarchy's native software-rendering detection automatically handles QEMU/VM sessions.
* **CPUs, Wi-Fi & Keymap**:
  * Dual `amd-ucode` + `intel-ucode` microcode, full `linux-firmware-*`, `NetworkManager`, and `keyd` (`leftmeta` tap mapped to `F24` -> Omarchy launcher).
  * Hybrid ISO supporting **UEFI + GPT**, **Legacy BIOS + GPT** (`bios_grub`), and **Legacy BIOS + MBR (`msdos`)**.

---

## Btrfs & Timeshift Snapshots

* **Default Btrfs Subvolumes**: Calamares provisions `@` (`/`), `@home` (`/home`), `@cache` (`/var/cache`), `@log` (`/var/log`), and `@swap` (`/swap`).
* **Timeshift + Autosnap (`timeshift`, `timeshift-autosnap`)**: Pre-configured in **BTRFS mode** with `00-timeshift-autosnap.hook` taking automatic snapshots before `pacman` upgrades.
* **Bootable GRUB Snapshots (`grub-btrfs`)**: `grub-btrfsd.service` watches snapshots and updates GRUB snapshot boot entries under `"HyprFrost Snapshots"`.

---

## Repository Structure

```
archinstall/
├── README.md
└── iso/
    ├── pkgbuilds/                         # Local PKGBUILDs built from jacobdt23/omarchy (jacob-rtx5070)
    │   ├── omarchy-keyring/
    │   ├── omarchy-settings-custom/
    │   └── omarchy-custom/
    ├── custom-repo/                       # Local pacman repo (Calamares, Paru, Timeshift-Autosnap, built Omarchy pkgs)
    ├── configs/
    │   └── archiso-profile/               # Archiso profile (pacman.conf, packages.x86_64, profiledef.sh, airootfs/)
    └── scripts/
        ├── build-custom-repo.sh           # AUR package builder for Calamares / Paru / Timeshift-Autosnap
        ├── build-omarchy-repo.sh          # Builds omarchy-keyring, omarchy-settings-custom, and omarchy-custom
        └── build-iso.sh                   # Native (sudo mkarchiso) or Podman/Docker ISO builder
```

---

## Building the Custom ISO

Build locally on Arch Linux (automatically rebuilds `omarchy-*` packages from [`jacobdt23/omarchy`](https://github.com/jacobdt23/omarchy) branch `jacob-rtx5070` and invokes `mkarchiso`):

```bash
sudo ./iso/scripts/build-iso.sh
```

Or run rootless `podman` / `docker` from any Linux distro. The compiled bootable ISO (`hyprfrost-YYYY.MM.DD-x86_64.iso`) is written to `iso/out/`.
