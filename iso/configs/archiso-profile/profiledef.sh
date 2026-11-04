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
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/usr/local/bin/Hyprland"]="0:0:755"
  ["/usr/local/bin/list-desktop-apps"]="0:0:755"
  ["/usr/local/bin/launch-calamares"]="0:0:755"
  ["/usr/local/bin/jacob-welcome"]="0:0:755"
  ["/usr/local/bin/jacob-shell"]="0:0:755"
  ["/usr/local/bin/jacob-control-center"]="0:0:755"
  ["/usr/local/bin/timeshift-launcher"]="0:0:755"
  ["/usr/local/bin/calamares-post-install"]="0:0:755"
  ["/usr/local/bin/calamares-find-rootfs"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
)
