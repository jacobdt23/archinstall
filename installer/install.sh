#!/bin/bash
set -e

# --- Prerequisites Check ---
if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this script as root."
    exit 1
fi

if [ ! -d "/sys/firmware/efi" ]; then
    echo "[-] System is not booted in UEFI mode. This script requires UEFI."
    exit 1
fi

if ! ping -c 1 archlinux.org &> /dev/null; then
    echo "[-] No internet connection. Please connect to the internet and try again."
    exit 1
fi

echo "[+] Prerequisites met. Starting installation..."

# --- User Inputs ---
read -p "Enter your preferred keyboard layout (e.g., us): " kblayout
loadkeys ${kblayout:-us}

echo "Available disks:"
lsblk -d -o NAME,SIZE,MODEL
read -p "Enter the target disk (e.g., /dev/sda or /dev/nvme0n1): " DISK
if [ ! -b "$DISK" ]; then
    echo "[-] Invalid disk device: $DISK"
    exit 1
fi

read -p "Enter hostname: " HOSTNAME
read -p "Enter username for regular user: " USERNAME
read -s -p "Enter password for user and root: " PASSWORD
echo
read -s -p "Confirm password: " PASSWORD_CONFIRM
echo

if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
    echo "[-] Passwords do not match."
    exit 1
fi

echo "Select a desktop environment to install:"
echo "1) KDE Plasma & Hyprland (Custom Default)"
echo "2) GNOME"
echo "3) XFCE"
echo "4) None (Base CLI only)"
read -p "Enter your choice (1-4): " de_choice

# --- Partitioning & Formatting ---
echo "[+] Partitioning disk $DISK..."
parted "$DISK" --script mklabel gpt
parted "$DISK" --script mkpart primary fat32 1MiB 512MiB
parted "$DISK" --script set 1 esp on
parted "$DISK" --script mkpart primary linux-swap 512MiB 4.5GiB
parted "$DISK" --script mkpart primary ext4 4.5GiB 100%

# Handle partition naming conventions (e.g., nvme0n1p1 vs sda1)
if [[ "$DISK" =~ "nvme" ]]; then
    PART_PREFIX="${DISK}p"
else
    PART_PREFIX="$DISK"
fi

EFIPART="${PART_PREFIX}1"
SWAPPART="${PART_PREFIX}2"
ROOTPART="${PART_PREFIX}3"

echo "[+] Formatting partitions..."
mkfs.fat -F32 "$EFIPART"
mkswap "$SWAPPART"
mkfs.ext4 "$ROOTPART"

echo "[+] Mounting partitions..."
mount "$ROOTPART" /mnt
mkdir -p /mnt/boot
mount "$EFIPART" /mnt/boot
swapon "$SWAPPART"

# --- System Installation ---
echo "[+] Updating system clock and installing base system..."
timedatectl set-ntp true
pacstrap /mnt base linux linux-firmware sudo git base-devel

echo "[+] Generating fstab..."
genfstab -U /mnt >> /mnt/etc/fstab

# --- Chroot Configuration ---
echo "[+] Entering chroot for system configuration..."
arch-chroot /mnt /bin/bash <<EOF
set -e

# Timezone & Localization
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
hwclock --systohc
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf

# Hostname & Hosts
echo "$HOSTNAME" > /etc/hostname
cat <<EOL > /etc/hosts
127.0.0.1   localhost
::1         localhost
127.0.1.1   $HOSTNAME.localdomain $HOSTNAME
EOL

# Passwords
echo "root:$PASSWORD" | chpasswd
useradd -m -G wheel -s /bin/bash "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd
echo "%wheel ALL=(ALL) ALL" >> /etc/sudoers

# Bootloader
pacman -S --noconfirm grub efibootmgr
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg

# Desktop Environment & Services Selection
case $de_choice in
    1)
        echo "[+] Installing KDE Plasma, Wayland, and Hyprland..."
        pacman -S --noconfirm xorg plasma kde-applications wayland hyprland-meta sddm networkmanager
        systemctl enable sddm.service
        ;;
    2)
        echo "[+] Installing GNOME..."
        pacman -S --noconfirm gnome gnome-extra gdm networkmanager
        systemctl enable gdm.service
        ;;
    3)
        echo "[+] Installing XFCE..."
        pacman -S --noconfirm xfce4 xfce4-goodies lightdm lightdm-gtk-greeter networkmanager
        systemctl enable lightdm.service
        ;;
    4)
        echo "[+] Skipping desktop environment. Installing NetworkManager..."
        pacman -S --noconfirm networkmanager
        ;;
esac

systemctl enable NetworkManager.service
mkinitcpio -P
EOF

# --- Cleanup & Reboot ---
echo "[+] Installation complete! Cleaning up mounts..."
umount -R /mnt
swapoff "$SWAPPART"

echo "[+] You can now safely reboot into your new system."
read -p "Press Enter to reboot..."
reboot
