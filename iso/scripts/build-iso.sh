#!/usr/bin/env bash
set -euo pipefail

# Build the Orbit OS Live/Install ISO (Hyprland + Qtile, no COSMIC)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${SCRIPT_DIR}/work"
OUT_DIR="${SCRIPT_DIR}/out"

if [[ $EUID -ne 0 ]]; then
    echo "Running mkarchiso via sudo..."
    exec sudo "$0" "$@"
fi

rm -rf "${WORK_DIR}"
mkdir -p "${OUT_DIR}"

mkarchiso -v -w "${WORK_DIR}" -o "${OUT_DIR}" "${SCRIPT_DIR}/../configs/archiso-profile"
echo ""
echo "ISO built successfully in: ${OUT_DIR}"
ls -lh "${OUT_DIR}"/*.iso
