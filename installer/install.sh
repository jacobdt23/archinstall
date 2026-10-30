#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKEL_SRC="$REPO_ROOT/iso/configs/archiso-profile/airootfs/etc/skel/.config"
if [ ! -d "$SKEL_SRC" ] && [ -d "/etc/skel/.config" ]; then
    SKEL_SRC="/etc/skel/.config"
fi

# --- Prerequisites Check ---
if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this script as root."
    exit 1
fi

if [ -d "/sys/firmware/efi" ]; then
    BOOT_MODE="UEFI"
else
    BOOT_MODE="BIOS"
fi

if ! ping -c 1 -W 3 archlinux.org &> /dev/null; then
    echo "[-] No internet connection. Please connect to the internet (e.g., via iwctl or nmtui) and try again."
    exit 1
fi

echo "==================================================================="
echo "   Jacob's Custom Arch Linux Installer (UEFI/BIOS • GPT/MBR)       "
echo "   Detected Firmware Mode: $BOOT_MODE                              "
echo "==================================================================="

# --- User Inputs ---
read -r -p "Enter preferred keyboard layout [default: us]: " kblayout
kblayout="${kblayout:-us}"
loadkeys "$kblayout" || true

read -r -p "Enter timezone [default: America/New_York]: " TIMEZONE
TIMEZONE="${TIMEZONE:-America/New_York}"
if [ ! -f "/usr/share/zoneinfo/$TIMEZONE" ]; then
    echo "[!] Timezone '$TIMEZONE' not found, falling back to UTC."
    TIMEZONE="UTC"
fi

echo
echo "Available disks:"
lsblk -d -o NAME,SIZE,MODEL,TYPE
echo
read -r -p "Enter the target disk (e.g., /dev/sda or /dev/nvme0n1): " DISK
if [ ! -b "$DISK" ]; then
    echo "[-] Invalid block device: $DISK"
    exit 1
fi

echo
echo "Select partition table & boot scheme:"
if [ "$BOOT_MODE" = "UEFI" ]; then
    echo "1) UEFI + GPT (512MiB EFI, 4GiB Swap, ext4 Root) [Recommended for UEFI]"
    echo "2) Legacy BIOS + GPT (2MiB BIOS Boot, 4GiB Swap, ext4 Root)"
    echo "3) Legacy BIOS + MBR/msdos (4GiB Swap, ext4 Root)"
    read -r -p "Enter choice [1-3, default: 1]: " part_scheme
    part_scheme="${part_scheme:-1}"
else
    echo "1) UEFI + GPT (512MiB EFI, 4GiB Swap, ext4 Root)"
    echo "2) Legacy BIOS + GPT (2MiB BIOS Boot, 4GiB Swap, ext4 Root) [Recommended for BIOS]"
    echo "3) Legacy BIOS + MBR/msdos (4GiB Swap, ext4 Root)"
    read -r -p "Enter choice [1-3, default: 2]: " part_scheme
    part_scheme="${part_scheme:-2}"
fi

read -r -p "WARNING: All data on $DISK will be erased! Type 'YES' to confirm: " CONFIRM_WIPE
if [ "$CONFIRM_WIPE" != "YES" ]; then
    echo "[-] Installation aborted."
    exit 1
fi

read -r -p "Enter hostname [default: jacob-arch]: " HOSTNAME
HOSTNAME="${HOSTNAME:-jacob-arch}"

read -r -p "Enter username [default: jacob]: " USERNAME
USERNAME="${USERNAME:-jacob}"

while true; do
    read -r -s -p "Enter password for $USERNAME and root: " PASSWORD
    echo
    read -r -s -p "Confirm password: " PASSWORD_CONFIRM
    echo
    if [ -n "$PASSWORD" ] && [ "$PASSWORD" = "$PASSWORD_CONFIRM" ]; then
        break
    fi
    echo "[-] Passwords do not match or are empty. Please try again."
done

echo
echo "Select GPU driver stack to install:"
echo "1) All Vendors: NVIDIA + AMD + Intel (Universal hardware compatibility - Default)"
echo "2) NVIDIA only (nvidia-open, nvidia-utils, CUDA/NVDEC VAAPI)"
echo "3) AMD only (mesa, vulkan-radeon, xf86-video-amdgpu)"
echo "4) Intel only (mesa, vulkan-intel, intel-media-driver)"
read -r -p "Enter choice [1-4, default: 1]: " gpu_choice
gpu_choice="${gpu_choice:-1}"

case "$gpu_choice" in
    2) GPU_PKGS=(mesa nvidia-open nvidia-utils nvidia-settings libva-nvidia-driver egl-wayland vulkan-icd-loader) ;;
    3) GPU_PKGS=(mesa vulkan-radeon xf86-video-amdgpu xf86-video-ati vulkan-icd-loader) ;;
    4) GPU_PKGS=(mesa vulkan-intel intel-media-driver libva-intel-driver xf86-video-intel vulkan-icd-loader) ;;
    *) GPU_PKGS=(mesa nvidia-open nvidia-utils nvidia-settings libva-nvidia-driver egl-wayland vulkan-radeon xf86-video-amdgpu xf86-video-ati vulkan-intel intel-media-driver libva-intel-driver xf86-video-intel vulkan-icd-loader) ;;
esac

echo
echo "Select a desktop profile to install:"
echo "1) Jacob's Custom Hyprland + Quickshell + XFCE Fallback (Default)"
echo "2) KDE Plasma + Wayland"
echo "3) GNOME"
echo "4) XFCE"
echo "5) None (Base CLI only)"
read -r -p "Enter your choice [1-5, default: 1]: " de_choice
de_choice="${de_choice:-1}"

# --- Partitioning & Formatting ---
if [[ "$DISK" =~ (nvme|mmcblk|loop) ]]; then
    PART_PREFIX="${DISK}p"
else
    PART_PREFIX="$DISK"
fi

wipefs -af "$DISK"

if [ "$part_scheme" = "1" ]; then
    echo "[+] Partitioning $DISK with GPT for UEFI (512MiB ESP, 4GiB Swap, Rest Root)..."
    parted "$DISK" --script mklabel gpt
    parted "$DISK" --script mkpart ESP fat32 1MiB 513MiB
    parted "$DISK" --script set 1 esp on
    parted "$DISK" --script mkpart primary linux-swap 513MiB 4609MiB
    parted "$DISK" --script mkpart primary ext4 4609MiB 100%
    partprobe "$DISK" || true
    sleep 1

    EFIPART="${PART_PREFIX}1"
    SWAPPART="${PART_PREFIX}2"
    ROOTPART="${PART_PREFIX}3"

    mkfs.fat -F32 "$EFIPART"
    mkswap "$SWAPPART"
    mkfs.ext4 -F "$ROOTPART"

    mount "$ROOTPART" /mnt
    mkdir -p /mnt/boot
    mount "$EFIPART" /mnt/boot
    swapon "$SWAPPART"
elif [ "$part_scheme" = "2" ]; then
    echo "[+] Partitioning $DISK with GPT for Legacy BIOS (2MiB bios_grub, 4GiB Swap, Rest Root)..."
    parted "$DISK" --script mklabel gpt
    parted "$DISK" --script mkpart primary 1MiB 3MiB
    parted "$DISK" --script set 1 bios_grub on
    parted "$DISK" --script mkpart primary linux-swap 3MiB 4099MiB
    parted "$DISK" --script mkpart primary ext4 4099MiB 100%
    partprobe "$DISK" || true
    sleep 1

    SWAPPART="${PART_PREFIX}2"
    ROOTPART="${PART_PREFIX}3"

    mkswap "$SWAPPART"
    mkfs.ext4 -F "$ROOTPART"

    mount "$ROOTPART" /mnt
    swapon "$SWAPPART"
else
    echo "[+] Partitioning $DISK with MBR (msdos) for Legacy BIOS (4GiB Swap, Rest Root)..."
    parted "$DISK" --script mklabel msdos
    parted "$DISK" --script mkpart primary linux-swap 1MiB 4097MiB
    parted "$DISK" --script mkpart primary ext4 4097MiB 100%
    parted "$DISK" --script set 2 boot on
    partprobe "$DISK" || true
    sleep 1

    SWAPPART="${PART_PREFIX}1"
    ROOTPART="${PART_PREFIX}2"

    mkswap "$SWAPPART"
    mkfs.ext4 -F "$ROOTPART"

    mount "$ROOTPART" /mnt
    swapon "$SWAPPART"
fi

# --- System Installation ---
echo "[+] Updating system clock and installing base system + CPU/GPU drivers..."
timedatectl set-ntp true
pacstrap -K /mnt base base-devel linux linux-firmware amd-ucode intel-ucode \
    "${GPU_PKGS[@]}" pciutils \
    sudo git vim micro btop fastfetch ripgrep curl wget zsh grml-zsh-config \
    networkmanager openssh grub efibootmgr dosfstools mtools

echo "[+] Generating fstab..."
genfstab -U /mnt >> /mnt/etc/fstab

# Configure NVIDIA DRM modeset for Wayland/Hyprland compatibility
mkdir -p /mnt/etc/modprobe.d
echo "options nvidia_drm modeset=1 fbdev=1" > /mnt/etc/modprobe.d/nvidia.conf

# Deploy custom pacman.conf if present
if [ -f "$SCRIPT_DIR/configs/pacman.conf" ]; then
    cp "$SCRIPT_DIR/configs/pacman.conf" /mnt/etc/pacman.conf
fi

# Deploy custom dotfiles to /mnt/etc/skel/.config
if [ -d "$SKEL_SRC" ]; then
    echo "[+] Deploying Jacob's custom desktop configs to /etc/skel/.config..."
    mkdir -p /mnt/etc/skel/.config
    cp -r "$SKEL_SRC/"* /mnt/etc/skel/.config/
    chmod +x /mnt/etc/skel/.config/hypr/wallpaper_loop.sh 2>/dev/null || true
fi

# --- Chroot Configuration ---
echo "[+] Configuring system inside arch-chroot..."
arch-chroot /mnt /bin/bash <<EOF
set -euo pipefail

# Timezone & Localization
ln -sf "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime
hwclock --systohc
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
grep -q "^en_US.UTF-8 UTF-8" /etc/locale.gen || echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
echo "KEYMAP=$kblayout" > /etc/vconsole.conf

# Hostname & Hosts
echo "$HOSTNAME" > /etc/hostname
cat <<EOL > /etc/hosts
127.0.0.1   localhost
::1         localhost
127.0.1.1   $HOSTNAME.localdomain $HOSTNAME
EOL

# Users & Sudoers
echo "root:$PASSWORD" | chpasswd
useradd -m -G wheel,video,audio,input,storage -s /bin/bash "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd
echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/wheel
chmod 0440 /etc/sudoers.d/wheel

# Copy custom dotfiles to new user's home directory
if [ -d "/etc/skel/.config" ]; then
    mkdir -p "/home/$USERNAME/.config"
    cp -r /etc/skel/.config/* "/home/$USERNAME/.config/"
    chown -R "$USERNAME:$USERNAME" "/home/$USERNAME/.config"
fi

# Bootloader Installation (UEFI vs BIOS/MBR/GPT)
if [ "$part_scheme" = "1" ]; then
    if [ -d "/sys/firmware/efi" ]; then
        grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB || true
    fi
    grub-install --target=x86_64-efi --efi-directory=/boot --removable
else
    grub-install --target=i386-pc "$DISK"
fi
grub-mkconfig -o /boot/grub/grub.cfg

# Desktop Environment & Services Selection
case "$de_choice" in
    1)
        echo "[+] Installing Jacob's Custom Hyprland + Quickshell + XFCE Desktop Stack..."
        pacman -S --noconfirm --needed \
            hyprland hyprlock hyprpaper hyprpolkitagent xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
            quickshell waybar awww alacritty kitty wl-clipboard cliphist libnotify playerctl polkit \
            qt5-wayland qt6-wayland qt6-5compat qt6-declarative \
            ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji \
            xfce4 xfce4-goodies thunar thunar-archive-plugin thunar-volman tumbler \
            lightdm lightdm-gtk-greeter network-manager-applet \
            bluez bluez-utils blueman \
            pipewire pipewire-pulse pipewire-alsa pipewire-jack wireplumber pavucontrol \
            firefox vlc obs-studio ncdu
        sed -i 's/^#user-session=.*/user-session=hyprland/' /etc/lightdm/lightdm.conf || true
        systemctl enable lightdm.service
        systemctl enable bluetooth.service
        ;;
    2)
        echo "[+] Installing KDE Plasma..."
        pacman -S --noconfirm --needed plasma kde-applications sddm \
            pipewire pipewire-pulse wireplumber firefox
        systemctl enable sddm.service
        ;;
    3)
        echo "[+] Installing GNOME..."
        pacman -S --noconfirm --needed gnome gnome-extra gdm \
            pipewire pipewire-pulse wireplumber firefox
        systemctl enable gdm.service
        ;;
    4)
        echo "[+] Installing XFCE..."
        pacman -S --noconfirm --needed xfce4 xfce4-goodies lightdm lightdm-gtk-greeter \
            pipewire pipewire-pulse wireplumber firefox
        systemctl enable lightdm.service
        ;;
    5)
        echo "[+] Base CLI profile selected (skipping GUI packages)."
        ;;
esac

systemctl enable NetworkManager.service
systemctl enable sshd.service
mkinitcpio -P
EOF

# --- Cleanup & Reboot ---
echo "[+] Installation complete! Unmounting filesystems..."
umount -R /mnt
swapoff "$SWAPPART"

echo "[+] Jacob's Custom Arch Linux is installed and ready."
read -r -p "Press Enter to reboot (or Ctrl+C to stay in live shell)..."
reboot
