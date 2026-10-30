# fix for screen readers
if grep -Fqa 'accessibility=' /proc/cmdline &> /dev/null; then
    setopt SINGLE_LINE_ZLE
fi

~/.automated_script.sh

# Automatically launch Jacob's Custom Hyprland + Quickshell desktop on first boot (tty1)
if [[ "$(tty)" == "/dev/tty1" ]] && [[ -z "${DISPLAY:-}" ]] && [[ -z "${WAYLAND_DISPLAY:-}" ]] && [[ ! -f /tmp/.hyprland_autostarted ]] && ! grep -Fqa 'accessibility=' /proc/cmdline &> /dev/null; then
    touch /tmp/.hyprland_autostarted
    /usr/local/bin/Hyprland
fi
