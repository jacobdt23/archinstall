# Custom Arch Linux ISO Build

This directory contains the configurations and build scripts for generating a custom, UEFI-compatible Arch Linux live ISO image using `mkarchiso`.

## Project Directory Structure

- **configs/archiso-profile/**: Contains the custom profile definition, package manifests, and live environment configurations.
  - **airootfs/**: Files and configurations overlaid onto the live environment root (including user dotfiles, shell configs, and systemd services).
  - **packages.x86_64**: List of packages installed in the custom ISO.
  - **grub/**: Custom GRUB bootloader configuration (`grub.cfg`) for UEFI booting.
  - **profiledef.sh**: Profile metadata and file permission definitions for `mkarchiso`.

- **scripts/**: Build automation scripts.
  - **build-iso.sh**: Main script that handles environment cleanup and invokes `mkarchiso` using absolute paths.

- **out/**: Output directory where the compiled custom ISO image is saved (`archlinux-*.iso`).

- **work/**: Temporary working directory generated during the `mkarchiso` build process.

## Usage

1. **Build the ISO**:
   From the repository root, run the build script with root privileges:
   ```bash
   sudo ./iso/scripts/build-iso.sh
## Usage (cont.)

2. **Locate your finished ISO**:
   The compiled image will be placed in `iso/out/`.

## Requirements

- An active internet connection and root privileges to run `mkarchiso`.
- Arch ISO build tools installed (`arch-install-scripts`, `archiso`).

## Notes

- Modify `iso/configs/archiso-profile/packages.x86_64` to adjust the package manifest included in your live environment.
- The ISO is built specifically for UEFI boot modes (`uefi.grub`).
