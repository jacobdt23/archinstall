#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$ISO_ROOT")"

PROFILE_DIR="$ISO_ROOT/configs/archiso-profile"
CUSTOM_REPO_DIR="$ISO_ROOT/custom-repo"
WORK_DIR="$ISO_ROOT/work"
OUT_DIR="$ISO_ROOT/out"

cleanup_staging() {
    if [ -L /repo/iso/custom-repo ]; then
        rm -f /repo/iso/custom-repo
    fi
}
trap cleanup_staging EXIT

echo "[+] Cleaning previous build directories..."
rm -rf "$WORK_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

if [ "${SKIP_OMARCHY_REPO_BUILD:-0}" != "1" ]; then
    echo "[+] Building Omarchy custom packages (omarchy-keyring, omarchy-settings-custom, omarchy-custom)..."
    bash "$SCRIPT_DIR/build-omarchy-repo.sh"
fi

echo "[+] Preparing executable scripts in live ISO airootfs..."
chmod +x "$PROFILE_DIR"/airootfs/usr/local/bin/* "$PROFILE_DIR/airootfs/root/customize_airootfs.sh"

if command -v mkarchiso >/dev/null 2>&1; then
    if [ "$EUID" -ne 0 ]; then
        echo "[-] Native mkarchiso requires root privileges. Please run: sudo $0"
        exit 1
    fi
    echo "[+] Building custom Arch ISO natively with mkarchiso..."
    mkdir -p /repo/iso
    ln -sfn "$CUSTOM_REPO_DIR" /repo/iso/custom-repo
    mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"
elif command -v podman >/dev/null 2>&1; then
    echo "[+] Non-Arch host detected. Building custom Arch ISO inside Arch Linux Podman container..."
    podman run --rm --privileged \
        -v "$REPO_ROOT:/repo:Z" \
        docker.io/library/archlinux:latest \
        /bin/bash -c "set -e
            sed -i 's/^#DisableSandbox/DisableSandbox/' /etc/pacman.conf
            pacman -Sy --noconfirm archiso arch-install-scripts grub base-devel git imagemagick
            bash /repo/iso/scripts/build-omarchy-repo.sh
            sed -i 's/setup=chroot_setup/setup=unshare_setup/' /usr/bin/pacstrap
            rm -rf /tmp/archiso-work
            mkarchiso -v -w /tmp/archiso-work -o /repo/iso/out /repo/iso/configs/archiso-profile"
elif command -v docker >/dev/null 2>&1; then
    echo "[+] Non-Arch host detected. Building custom Arch ISO inside Arch Linux Docker container..."
    docker run --rm --privileged \
        -v "$REPO_ROOT:/repo" \
        docker.io/library/archlinux:latest \
        /bin/bash -c "set -e
            sed -i 's/^#DisableSandbox/DisableSandbox/' /etc/pacman.conf
            pacman -Sy --noconfirm archiso arch-install-scripts grub base-devel git imagemagick
            bash /repo/iso/scripts/build-omarchy-repo.sh
            sed -i 's/setup=chroot_setup/setup=unshare_setup/' /usr/bin/pacstrap
            rm -rf /tmp/archiso-work
            mkarchiso -v -w /tmp/archiso-work -o /repo/iso/out /repo/iso/configs/archiso-profile"
else
    echo "[-] Neither mkarchiso nor podman/docker found. Install archiso (on Arch) or podman (on Fedora/other distros)."
    exit 1
fi

echo "[+] Build complete! Your custom ISO is located in: $OUT_DIR"
ls -lh "$OUT_DIR"/*.iso 2>/dev/null || true
