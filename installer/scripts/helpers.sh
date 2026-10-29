#!/bin/bash

# Install packages if not already installed
install_packages() {
    local packages=("$@")
    if [ ${#packages[@]} -gt 0 ]; then
        echo "[+] Installing packages: ${packages[*]}"
        pacman -S --noconfirm --needed "${packages[@]}"
    else
        echo "[-] No packages selected."
    fi
}

# Check if a package is installed
is_package_installed() {
    local package="$1"
    pacman -Q "$package" &> /dev/null
}

# Create a user with wheel/desktop groups
create_user() {
    local username="$1"
    if id "$username" &>/dev/null; then
        echo "[*] User $username already exists."
    else
        useradd -m -G wheel,video,audio,input,storage -s /bin/bash "$username"
        echo "[+] User $username created."
    fi
}

# Set password for a user
set_user_password() {
    local username="$1"
    passwd "$username"
}

# Enable a systemd service
enable_service() {
    local service="$1"
    systemctl enable "$service"
    echo "[+] Service $service enabled."
}

# Start a systemd service
start_service() {
    local service="$1"
    systemctl start "$service"
    echo "[+] Service $service started."
}

# Deploy Jacob's custom dotfiles to a target user
deploy_custom_dotfiles() {
    local username="$1"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local skel_src="$script_dir/../../../iso/configs/archiso-profile/airootfs/etc/skel/.config"
    if [ ! -d "$skel_src" ] && [ -d "/etc/skel/.config" ]; then
        skel_src="/etc/skel/.config"
    fi

    if [ -d "$skel_src" ] && [ -d "/home/$username" ]; then
        mkdir -p "/home/$username/.config"
        cp -r "$skel_src/"* "/home/$username/.config/"
        chmod +x "/home/$username/.config/hypr/wallpaper_loop.sh" 2>/dev/null || true
        chown -R "$username:$username" "/home/$username/.config"
        echo "[+] Deployed Jacob's custom Hyprland & Quickshell configs to /home/$username/.config"
    fi
}
