#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this script with sudo."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

PROFILE_DIR="$REPO_ROOT/configs/archiso-profile"
WORK_DIR="$REPO_ROOT/work"
OUT_DIR="$REPO_ROOT/out"

echo "[+] Cleaning previous build directories..."
rm -rf "$WORK_DIR" "$OUT_DIR"

echo "[+] Building custom Arch ISO with mkarchiso..."
mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"

echo "[+] Build complete! Your ISO is located in: $OUT_DIR"
