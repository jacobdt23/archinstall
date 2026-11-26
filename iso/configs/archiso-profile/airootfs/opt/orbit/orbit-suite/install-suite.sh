#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"

mkdir -p "${BIN_DIR}" "${APP_DIR}"

install_app() {
    local bin_name="$1"
    local module_name="$2"
    local desktop_id="$3"

    local bin_path="${BIN_DIR}/${bin_name}"
    local desktop_src="${PROJECT_DIR}/data/${desktop_id}.desktop"
    local desktop_dst="${APP_DIR}/${desktop_id}.desktop"

    cat > "${bin_path}" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${PROJECT_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m ${module_name} "\$@"
EOF
    chmod +x "${bin_path}"

    sed \
        -e "s|^Exec=${bin_name}|Exec=${bin_path}|g" \
        -e "s|^TryExec=${bin_name}|TryExec=${bin_path}|g" \
        "${desktop_src}" > "${desktop_dst}"

    if command -v desktop-file-validate >/dev/null 2>&1; then
        desktop-file-validate "${desktop_dst}"
    fi
    echo "Installed ${bin_name} -> ${desktop_dst}"
}

install_app "orbit-edit"   "orbit_suite.edit"   "dev.orbit.Edit"
install_app "orbit-view"   "orbit_suite.view"   "dev.orbit.View"
install_app "orbit-launch" "orbit_suite.launch" "dev.orbit.Launch"
install_app "orbit-term"   "orbit_suite.term"   "dev.orbit.Term"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}"
fi

if [[ "${1:-}" == "--set-defaults" ]]; then
    if command -v xdg-mime >/dev/null 2>&1; then
        [[ -f "${APP_DIR}/dev.orbit.Files.desktop" ]] && \
            xdg-mime default dev.orbit.Files.desktop inode/directory
        xdg-mime default dev.orbit.Edit.desktop \
            text/plain text/markdown text/x-python text/css text/x-shellscript application/json
        xdg-mime default dev.orbit.View.desktop \
            image/png image/jpeg image/webp image/gif image/bmp image/svg+xml
        echo "Registered Orbit Suite as default XDG handlers."
    fi
fi
