#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helpers.sh
source "$SCRIPT_DIR/helpers.sh"

if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this script as root (sudo $0)."
    exit 1
fi

connect_wifi() {
    echo "[*] Checking for active internet connection..."
    if ping -c 1 -W 3 archlinux.org &>/dev/null; then
        echo "[+] Internet connection is active."
    else
        echo "[-] No active internet connection detected."
        if command -v iwctl &>/dev/null; then
            echo "Starting iwctl for Wi-Fi setup..."
            echo "1. 'device list' -> 2. 'station <dev> scan' -> 3. 'station <dev> connect <SSID>' -> 4. 'exit'"
            iwctl
        elif command -v nmtui &>/dev/null; then
            nmtui
        else
            echo "[-] Neither iwctl nor nmtui found. Please connect to the internet first."
            exit 1
        fi
        if ! ping -c 1 -W 3 archlinux.org &>/dev/null; then
            echo "[-] Failed to establish internet connection."
            exit 1
        fi
    fi
}

setup_interactive_user() {
    read -r -p "Enter username to create/configure [default: jacob]: " username
    username="${username:-jacob}"
    create_user "$username"
    if ! passwd -S "$username" 2>/dev/null | grep -q " P "; then
        echo "Set a password for $username:"
        set_user_password "$username"
    fi
    echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/wheel
    chmod 0440 /etc/sudoers.d/wheel
    deploy_custom_dotfiles "$username"
}

install_desktop_menu() {
    echo "Select Desktop Environment:"
    echo "1) Jacob's Custom Hyprland + Quickshell Stack"
    echo "2) KDE Plasma"
    echo "3) GNOME"
    echo "4) XFCE"
    echo "5) LXQt"
    read -r -p "Enter choice [1-5]: " de_opt
    case "$de_opt" in
        1)
            install_packages nvidia-open nvidia-utils \
                hyprland hyprlock hyprpaper hyprpolkitagent xdg-desktop-portal-hyprland \
                quickshell waybar awww alacritty kitty wl-clipboard cliphist libnotify playerctl \
                qt5-wayland qt6-wayland qt6-5compat qt6-declarative \
                ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji \
                thunar thunar-archive-plugin thunar-volman tumbler \
                lightdm lightdm-gtk-greeter network-manager-applet
            sed -i 's/^#user-session=.*/user-session=hyprland/' /etc/lightdm/lightdm.conf || true
            enable_service lightdm.service
            ;;
        2)
            install_packages plasma kde-applications sddm
            enable_service sddm.service
            ;;
        3)
            install_packages gnome gnome-extra gdm
            enable_service gdm.service
            ;;
        4)
            install_packages xfce4 xfce4-goodies lightdm lightdm-gtk-greeter
            enable_service lightdm.service
            ;;
        5)
            install_packages lxqt breeze-icons sddm
            enable_service sddm.service
            ;;
        *)
            echo "[-] Invalid selection."
            ;;
    esac
}

configure_system() {
    echo "Configure System Settings:"
    echo "1) Set Locale (en_US.UTF-8)"
    echo "2) Set Timezone (America/New_York)"
    echo "3) Optimize Pacman Mirrors (Reflector)"
    echo "4) Enable Core Services (NetworkManager, Bluetooth, SSH)"
    read -r -p "Enter your choice [1-4]: " config_choice
    case "$config_choice" in
        1)
            sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
            grep -q "^en_US.UTF-8 UTF-8" /etc/locale.gen || echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
            locale-gen
            echo "LANG=en_US.UTF-8" > /etc/locale.conf
            echo "[+] Locale configured."
            ;;
        2)
            read -r -p "Enter timezone [default: America/New_York]: " tz
            tz="${tz:-America/New_York}"
            ln -sf "/usr/share/zoneinfo/$tz" /etc/localtime
            hwclock --systohc
            echo "[+] Timezone set to $tz."
            ;;
        3)
            install_packages reflector
            reflector --country "United States" --latest 10 --sort rate --save /etc/pacman.d/mirrorlist
            echo "[+] Mirrors updated."
            ;;
        4)
            install_packages networkmanager bluez bluez-utils openssh
            enable_service NetworkManager.service
            enable_service bluetooth.service
            enable_service sshd.service
            ;;
        *)
            echo "[-] Invalid choice."
            ;;
    esac
}

show_menu() {
    echo
    echo "==================================================="
    echo "   Jacob's Custom Arch Linux Modular Setup Menu    "
    echo "==================================================="
    echo "1) Install Base System Utilities"
    echo "2) Install Desktop Environment (Hyprland / KDE / GNOME / XFCE)"
    echo "3) Install Web Browsers (Firefox, Chromium)"
    echo "4) Install Media & Audio Stack (PipeWire, VLC, MPV, OBS)"
    echo "5) Install Development Tools (base-devel, git, vim, micro)"
    echo "6) Install System Utilities (btop, fastfetch, ncdu, ripgrep)"
    echo "7) Create User & Deploy Jacob's Custom Dotfiles"
    echo "8) Configure System Settings (Locale, Timezone, Mirrors, Services)"
    echo "9) Run Post-Install Finalization"
    echo "10) Exit"
    echo "==================================================="
}

connect_wifi

while true; do
    show_menu
    read -r -p "Select an option [1-10]: " choice
    case "$choice" in
        1) install_packages base base-devel linux-firmware sudo networkmanager grub efibootmgr ;;
        2) install_desktop_menu ;;
        3) install_packages firefox chromium ;;
        4) install_packages pipewire pipewire-pulse pipewire-alsa wireplumber pavucontrol vlc mpv obs-studio ;;
        5) install_packages base-devel git vim micro curl wget ;;
        6) install_packages btop fastfetch ncdu ripgrep zsh grml-zsh-config ;;
        7) setup_interactive_user ;;
        8) configure_system ;;
        9) "$SCRIPT_DIR/post-install.sh" ;;
        10) echo "[+] Exiting installer."; exit 0 ;;
        *) echo "[-] Invalid option: $choice" ;;
    esac
done
