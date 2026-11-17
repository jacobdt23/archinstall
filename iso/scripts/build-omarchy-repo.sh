#!/usr/bin/env bash
# =============================================================================
# Build Omarchy custom packages (omarchy-keyring, omarchy-settings-custom,
# omarchy-custom) from jacobdt23/omarchy into iso/custom-repo and refresh DB.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PKGBUILDS_DIR="$ISO_ROOT/pkgbuilds"
CUSTOM_REPO="$ISO_ROOT/custom-repo"
BUILD_TMP="/tmp/hyprfrost-omarchy-build"

export OMARCHY_REPO="${OMARCHY_REPO:-https://github.com/jacobdt23/omarchy.git}"
export OMARCHY_BRANCH="${OMARCHY_BRANCH:-jacob-rtx5070}"

mkdir -p "$CUSTOM_REPO"

# Remove retired non-Omarchy desktop AUR artifacts if still present
rm -f \
    "$CUSTOM_REPO"/waypaper-*.pkg.tar.* \
    "$CUSTOM_REPO"/python-imageio-ffmpeg-*.pkg.tar.* \
    "$CUSTOM_REPO"/python-screeninfo-*.pkg.tar.*

# Ensure build dependencies exist on the build host before dropping privileges
for tool in git magick repo-add makepkg; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[-] Missing required build tool: $tool" >&2
        if [ "$EUID" -eq 0 ]; then
            pacman -S --needed --noconfirm base-devel git imagemagick pacman
            break
        else
            echo "    Install base-devel, git, and imagemagick first." >&2
            exit 1
        fi
    fi
done

build_as_unprivileged() {
    local pkg_name="$1"
    local pkg_dir="$BUILD_TMP/$pkg_name"

    rm -rf "$pkg_dir"
    cp -a "$PKGBUILDS_DIR/$pkg_name" "$pkg_dir"

    if [ "$EUID" -eq 0 ]; then
        local build_user="${SUDO_USER:-}"
        if [ -z "$build_user" ] || [ "$build_user" = "root" ] || ! id -u "$build_user" >/dev/null 2>&1; then
            build_user="hyprfrost-builder"
            if ! id -u "$build_user" >/dev/null 2>&1; then
                useradd -m -s /bin/bash "$build_user"
            fi
        fi
        chown -R "$build_user:$build_user" "$pkg_dir"
        su - "$build_user" -s /bin/bash -c \
            "cd $(printf '%q' "$pkg_dir") && OMARCHY_REPO=$(printf '%q' "$OMARCHY_REPO") OMARCHY_BRANCH=$(printf '%q' "$OMARCHY_BRANCH") OMARCHY_SRC=$(printf '%q' "${OMARCHY_SRC:-}") makepkg -f --noconfirm --nodeps"
    else
        (cd "$pkg_dir" && makepkg -f --noconfirm --nodeps)
    fi

    rm -f "$CUSTOM_REPO/${pkg_name}-"*.pkg.tar.*
    find "$pkg_dir" -maxdepth 1 -type f -name '*.pkg.tar.*' ! -name '*.sig' ! -name '*-debug-*' \
        -exec cp -f {} "$CUSTOM_REPO/" \;
}

mkdir -p "$BUILD_TMP"
trap 'rm -rf "$BUILD_TMP"' EXIT

for pkg in omarchy-keyring omarchy-settings-custom omarchy-custom; do
    echo "[+] Building $pkg..."
    build_as_unprivileged "$pkg"
done

echo "[+] Refreshing customrepo database..."
rm -f "$CUSTOM_REPO"/customrepo.db* "$CUSTOM_REPO"/customrepo.files*
repo-add -R "$CUSTOM_REPO/customrepo.db.tar.gz" "$CUSTOM_REPO"/*.pkg.tar.zst

echo "[+] Done! Packages in $CUSTOM_REPO:"
ls -lh "$CUSTOM_REPO"/*.pkg.tar.zst
