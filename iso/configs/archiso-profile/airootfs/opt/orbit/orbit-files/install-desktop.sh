#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
BIN_PATH="${BIN_DIR}/orbit-files"
DESKTOP_SRC="${PROJECT_DIR}/data/dev.orbit.Files.desktop"
DESKTOP_DST="${APP_DIR}/dev.orbit.Files.desktop"

mkdir -p "${BIN_DIR}" "${APP_DIR}"

# 1. Install executable launcher wrapper into ~/.local/bin/orbit-files
cat > "${BIN_PATH}" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${PROJECT_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m orbit_files "\$@"
EOF
chmod +x "${BIN_PATH}"

# 2. Install .desktop entry with absolute Exec/TryExec so WM launchers always find it
sed \
    -e "s|^Exec=orbit-files|Exec=${BIN_PATH}|g" \
    -e "s|^TryExec=orbit-files|TryExec=${BIN_PATH}|g" \
    -e "s|exec orbit-files|exec ${BIN_PATH}|g" \
    "${DESKTOP_SRC}" > "${DESKTOP_DST}"

# 3. Validate the installed .desktop file
if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "${DESKTOP_DST}"
fi

# 4. Refresh the XDG desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}"
fi

echo "Installed launcher: ${BIN_PATH}"
echo "Installed desktop entry: ${DESKTOP_DST}"

# Optional: set Orbit Files as the default file manager for directories
if [[ "${1:-}" == "--set-default" ]]; then
    if command -v xdg-mime >/dev/null 2>&1; then
        xdg-mime default dev.orbit.Files.desktop inode/directory
        echo "Set Orbit Files as default handler for inode/directory."
    fi
fi
