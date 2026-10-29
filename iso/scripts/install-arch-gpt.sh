#!/bin/bash
set -euo pipefail

# Unattended/Quick GPT UEFI Arch Installer for Jacob's Custom Linux
DISK="${DISK:-/dev/sda}"
HOSTNAME="${HOSTNAME:-jacob-arch}"
USERNAME="${USERNAME:-jacob}"
PASSWORD="${PASSWORD:-jacob}"
TIMEZONE="${TIMEZONE:-America/New_York}"

if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run this script as root."
    exit 1
fi

if [ ! -b "$DISK" ]; then
    echo "[-] Target disk $DISK not found. Set DISK=/dev/nvme0n1 (or /dev/vda) and re-run."
    exit 1
fi

read -r -p "WARNING: This will format $DISK for user '$USERNAME'. Type 'YES' to continue: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
    echo "[-] Aborted."
    exit 1
fi

if [[ "$DISK" =~ (nvme|mmcblk|loop) ]]; then
    PART_PREFIX="${DISK}p"
else
    PART_PREFIX="$DISK"
fi

EFIPART="${PART_PREFIX}1"
SWAPPART="${PART_PREFIX}2"
ROOTPART="${PART_PREFIX}3"

echo "[+] Partitioning $DISK..."
wipefs -af "$DISK"
parted "$DISK" --script mklabel gpt
parted "$DISK" --script mkpart ESP fat32 1MiB 513MiB
parted "$DISK" --script set 1 esp on
parted "$DISK" --script mkpart primary linux-swap 513MiB 4609MiB
parted "$DISK" --script mkpart primary ext4 4609MiB 100%
partprobe "$DISK" || true
sleep 1

echo "[+] Formatting partitions..."
mkfs.fat -F32 "$EFIPART"
mkswap "$SWAPPART"
mkfs.ext4 -F "$ROOTPART"

echo "[+] Mounting partitions..."
mount "$ROOTPART" /mnt
mkdir -p /mnt/boot
mount "$EFIPART" /mnt/boot
swapon "$SWAPPART"

echo "[+] Installing base system and Jacob's Custom Hyprland + Quickshell stack..."
pacstrap -K /mnt base base-devel linux linux-firmware amd-ucode intel-ucode \
    sudo git vim micro btop fastfetch ripgrep curl wget zsh grml-zsh-config \
    networkmanager network-manager-applet openssh grub efibootmgr \
    hyprland hyprlock hyprpaper hyprpolkitagent xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
    quickshell waybar awww alacritty kitty wl-clipboard cliphist libnotify playerctl polkit \
    qt5-wayland qt6-wayland qt6-5compat qt6-declarative \
    ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji \
    xfce4 xfce4-goodies thunar thunar-archive-plugin thunar-volman tumbler \
    lightdm lightdm-gtk-greeter bluez bluez-utils blueman \
    pipewire pipewire-pulse pipewire-alsa pipewire-jack wireplumber pavucontrol firefox

echo "[+] Generating fstab..."
genfstab -U /mnt >> /mnt/etc/fstab

if [ -d "/etc/skel/.config" ]; then
    mkdir -p /mnt/etc/skel/.config
    cp -r /etc/skel/.config/* /mnt/etc/skel/.config/
fi

echo "[+] Entering chroot..."
arch-chroot /mnt /bin/bash <<EOF
set -euo pipefail

ln -sf "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime
hwclock --systohc
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
grep -q "^en_US.UTF-8 UTF-8" /etc/locale.gen || echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf

echo "$HOSTNAME" > /etc/hostname
cat <<EOL > /etc/hosts
127.0.0.1   localhost
::1         localhost
127.0.1.1   $HOSTNAME.localdomain $HOSTNAME
EOL

echo "root:$PASSWORD" | chpasswd

useradd -m -G wheel,video,audio,input,storage -s /bin/bash "$USERNAME"
echo "$USERNAME:$PASSWORD" | chpasswd
echo "%wheel ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel
chmod 0440 /etc/sudoers.d/wheel

if [ -d "/etc/skel/.config" ]; then
    mkdir -p "/home/$USERNAME/.config"
    cp -r /etc/skel/.config/* "/home/$USERNAME/.config/"
    chown -R "$USERNAME:$USERNAME" "/home/$USERNAME/.config"
fi

grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg

systemctl enable NetworkManager.service
systemctl enable lightdm.service
systemctl enable bluetooth.service
systemctl enable sshd.service
mkinitcpio -P
EOF

echo "[+] Installation complete. Unmounting..."
umount -R /mnt
swapoff -a
echo "[+] Done! You can now reboot."
