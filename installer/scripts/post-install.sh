#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helpers.sh
source "$SCRIPT_DIR/helpers.sh"

if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this script as root."
    exit 1
fi

echo "[+] Starting post-installation tasks..."

read -r -p "Enter username for the primary user [default: jacob]: " username
username="${username:-jacob}"

create_user "$username"
if ! passwd -S "$username" 2>/dev/null | grep -q " P "; then
    set_user_password "$username"
fi

echo "[+] Configuring sudoers..."
echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/wheel
chmod 0440 /etc/sudoers.d/wheel

echo "[+] Deploying custom Hyprland & Quickshell dotfiles..."
deploy_custom_dotfiles "$username"

echo "[+] Enabling core services..."
enable_service NetworkManager.service

echo "[+] Applying timezone settings (America/New_York)..."
ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
hwclock --systohc || true

echo "[+] Post-installation tasks completed!"
