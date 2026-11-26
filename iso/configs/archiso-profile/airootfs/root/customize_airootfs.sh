#!/usr/bin/env bash
set -euo pipefail

# Create unprivileged live desktop user for SDDM + Orbit Desktop (Hyprland)
if ! id -u orbit >/dev/null 2>&1; then
    useradd -m -G wheel,video,audio,input,render,storage -s /usr/bin/fish orbit
fi
passwd -d orbit

cp -a /etc/skel/. /home/orbit/
chown -R orbit:orbit /home/orbit

# Auto-launch Calamares on the live ISO desktop only (not in /etc/skel)
if [ -f /home/orbit/.config/hypr-standalone/hyprland.conf ]; then
    cat >> /home/orbit/.config/hypr-standalone/hyprland.conf <<'EOF'

-- Live ISO only: auto-launch Calamares graphical installer
hl.on("hyprland.start", function()
  hl.exec_cmd("/usr/local/bin/launch-calamares")
end)
EOF
    chown orbit:orbit /home/orbit/.config/hypr-standalone/hyprland.conf
fi
