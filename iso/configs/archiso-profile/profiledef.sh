#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="hyprfrost"
iso_label="HYPRFROST"
iso_publisher="HyprFrost <https://github.com/jacobdt23/archinstall>"
iso_application="HyprFrost Linux Live/Install ISO"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=(
  'bios.syslinux'
  'uefi.grub'
)
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/sudoers.d"]="0:0:750"
  ["/etc/sudoers.d/10-live-nopasswd"]="0:0:440"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/customize_airootfs.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/usr/local/bin/launch-calamares"]="0:0:755"
  ["/usr/local/bin/timeshift-launcher"]="0:0:755"
  ["/usr/local/bin/calamares-post-install"]="0:0:755"
  ["/usr/local/bin/calamares-find-rootfs"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
  ["/usr/local/bin/fix-boot-branding"]="0:0:755"
  ["/usr/local/bin/setup-zram"]="0:0:755"
  ["/usr/local/bin/pkg-install"]="0:0:755"
  ["/usr/local/bin/pkg-save"]="0:0:755"
)
