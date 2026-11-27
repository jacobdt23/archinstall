#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="orbit-os"
iso_label="ORBIT_OS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="Orbit Desktop <https://github.com/jacobdt23>"
iso_application="Orbit OS Live/Install ISO (Hyprland + Qtile)"
iso_version="1.0.0"
install_dir="arch"
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86,arm64' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
kernel_params_aarch64="clk_ignore_unused pd_ignore_unused arm64.nopauth"
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/sudoers.d/10-live-nopasswd"]="0:0:440"
  ["/etc/skel/.config/qtile/autostart.sh"]="0:0:755"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/usr/local/bin/calamares-find-rootfs"]="0:0:755"
  ["/usr/local/bin/calamares-post-install"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/fastfetch-session"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/launch-calamares"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
  ["/usr/local/bin/orbit-edit"]="0:0:755"
  ["/usr/local/bin/orbit-files"]="0:0:755"
  ["/usr/local/bin/orbit-launch"]="0:0:755"
  ["/usr/local/bin/orbit-live-setup"]="0:0:755"
  ["/usr/local/bin/orbit-nvim"]="0:0:755"
  ["/usr/local/bin/orbit-nvim-cli"]="0:0:755"
  ["/usr/local/bin/orbit-shell"]="0:0:755"
  ["/usr/local/bin/orbit-term"]="0:0:755"
  ["/usr/local/bin/orbit-theme"]="0:0:755"
  ["/usr/local/bin/orbit-view"]="0:0:755"
  ["/usr/local/bin/start-hyprland-standalone"]="0:0:755"
  ["/usr/local/bin/start-orbit-qtile"]="0:0:755"
)
