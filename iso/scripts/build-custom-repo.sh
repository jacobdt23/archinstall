#!/bin/bash
# =============================================================================
# HyprFrost Custom Repo Builder
# Builds AUR packages into iso/custom-repo/ and updates the repository database
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_ROOT="$(dirname "$SCRIPT_DIR")"
CUSTOM_REPO_DIR="$ISO_ROOT/custom-repo"
BUILD_TMP="/tmp/hyprfrost-repo-build"

# Default AUR packages required for HyprFrost live installer & desktop stack
DEFAULT_AUR_PACKAGES=(
    "calamares"
    "paru"
    "timeshift-autosnap"
    "waypaper"
    "python-imageio-ffmpeg"
    "python-screeninfo"
)

mkdir -p "$CUSTOM_REPO_DIR" "$BUILD_TMP"

PACKAGES_TO_BUILD=("$@")
if [ ${#PACKAGES_TO_BUILD[@]} -eq 0 ]; then
    PACKAGES_TO_BUILD=("${DEFAULT_AUR_PACKAGES[@]}")
fi

echo -e "\033[1;34m:: HyprFrost Custom Repository Builder\033[0m"
echo -e "   Target directory: $CUSTOM_REPO_DIR"
echo -e "   Packages: ${PACKAGES_TO_BUILD[*]}"
echo ""

for pkg in "${PACKAGES_TO_BUILD[@]}"; do
    echo -e "\033[1;36m:: Processing package: $pkg...\033[0m"
    PKG_WORK="$BUILD_TMP/$pkg"
    rm -rf "$PKG_WORK"

    echo "   Cloning PKGBUILD from AUR..."
    if ! git clone --depth 1 "https://aur.archlinux.org/${pkg}.git" "$PKG_WORK" 2>/dev/null; then
        echo -e "\033[1;31m[-] Failed to clone $pkg from AUR\033[0m"
        continue
    fi

    (
        cd "$PKG_WORK"
        echo "   Building $pkg package..."
        makepkg -scf --noconfirm
        echo "   Copying package archive to custom repo..."
        cp -f ./*.pkg.tar.zst "$CUSTOM_REPO_DIR/"
    )

    rm -rf "$PKG_WORK"
    echo -e "\033[1;32m✔ $pkg built successfully!\033[0m"
done

echo ""
echo -e "\033[1;33m:: Updating customrepo database with repo-add...\033[0m"
(
    cd "$CUSTOM_REPO_DIR"
    # Remove old database links if present
    rm -f customrepo.db customrepo.files
    # Add all packages to repo database
    repo-add -n -R customrepo.db.tar.gz ./*.pkg.tar.zst
    # Recreate symlinks
    ln -sf customrepo.db.tar.gz customrepo.db
    ln -sf customrepo.files.tar.gz customrepo.files
)

echo ""
echo -e "\033[1;32m✔ Custom repository updated successfully!\033[0m"
echo -e "\033[1;34m:: Current packages in $CUSTOM_REPO_DIR:\033[0m"
ls -lh "$CUSTOM_REPO_DIR"/*.pkg.tar.zst
