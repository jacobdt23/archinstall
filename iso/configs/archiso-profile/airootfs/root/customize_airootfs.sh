#!/usr/bin/env bash
set -euo pipefail

# Remove upstream Hyprland uwsm duplicate session if extracted before NoExtract took effect
rm -f /usr/share/wayland-sessions/hyprland-uwsm.desktop

# Create unprivileged live desktop user for SDDM + uwsm + Omarchy
if ! id -u hyprfrost >/dev/null 2>&1; then
    useradd -m -G wheel,video,audio,input,render,storage -s /usr/bin/bash hyprfrost
fi
passwd -d hyprfrost

cp -a /etc/skel/. /home/hyprfrost/
chown -R hyprfrost:hyprfrost /home/hyprfrost

# Generate offline mise system shims before unprivileged user provisioning
if command -v mise >/dev/null 2>&1; then
    MISE_OFFLINE=true mise reshim --system || true
fi

# Provision Omarchy live session state (Tokyo Night theme, desktop entries, skill links)
if [ -x /usr/share/omarchy/bin/omarchy-provision-user ]; then
    su - hyprfrost -c '
        export OMARCHY_PATH=/usr/share/omarchy
        export OMARCHY_SETUP_CONTEXT=iso-chroot
        export PATH="/usr/share/omarchy/bin:$PATH"
        /usr/share/omarchy/bin/omarchy-provision-user --force --first-install || true
        if [[ ! -s "$HOME/.local/state/omarchy/current/theme.name" ]] && command -v omarchy-theme-set >/dev/null 2>&1; then
            OMARCHY_THEME_HEADLESS=1 omarchy-theme-set "Tokyo Night" || true
        fi
    '
fi

# Pin Calamares graphical installer onto the live ISO Omarchy dock only (not /etc/skel)
if [ -f /home/hyprfrost/.config/omarchy/shell.json ] && command -v jq >/dev/null 2>&1; then
    tmp_json=$(mktemp)
    jq '.dock.pinned = (["calamares"] + ((.dock.pinned // []) | map(select(. != "calamares"))))' \
        /home/hyprfrost/.config/omarchy/shell.json >"$tmp_json" && \
        install -m 0644 -o hyprfrost -g hyprfrost "$tmp_json" /home/hyprfrost/.config/omarchy/shell.json
    rm -f "$tmp_json"
fi

# Launch Calamares automatically on the live ISO desktop (live user only; not /etc/skel)
if [ -d /home/hyprfrost/.config/hypr ]; then
    cat > /home/hyprfrost/.config/hypr/autostart.lua <<'EOF'
-- Live ISO autostart (not included in installed user accounts)
o.launch_on_start("launch-calamares")
EOF
    chown hyprfrost:hyprfrost /home/hyprfrost/.config/hypr/autostart.lua
fi

# Ensure HyprFrost OS identity on the live image
if [ -x /usr/local/bin/fix-boot-branding ]; then
    /usr/local/bin/fix-boot-branding || true
fi
