#!/bin/bash
set -euo pipefail

# Custom setup script for Jacob's Arch Linux environment
USERNAME="${USERNAME:-jacob}"
PASSWORD="${PASSWORD:-jacob}"

timedatectl set-ntp true || true

pacman -S --noconfirm --needed vim git openssh networkmanager

systemctl enable NetworkManager.service
systemctl enable sshd.service

if ! id "$USERNAME" &>/dev/null; then
    useradd -m -G wheel,video,audio,input,storage -s /bin/bash "$USERNAME"
    echo "$USERNAME:$PASSWORD" | chpasswd
fi

echo "%wheel ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel
chmod 0440 /etc/sudoers.d/wheel

if [ -d "/etc/skel/.config" ] && [ -d "/home/$USERNAME" ]; then
    mkdir -p "/home/$USERNAME/.config"
    cp -r /etc/skel/.config/* "/home/$USERNAME/.config/"
    chown -R "$USERNAME:$USERNAME" "/home/$USERNAME/.config"
fi

echo "[+] Custom setup completed for user '$USERNAME'."
