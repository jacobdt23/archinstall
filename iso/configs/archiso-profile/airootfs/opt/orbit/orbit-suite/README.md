# Orbit Suite

A cohesive suite of native **GTK 4 + Libadwaita** desktop apps written in Python to replace default Unix desktop apps in custom window managers (Hyprland, Sway, i3, River, Openbox, etc.):

- **Orbit Edit** (`orbit-edit`) — Multi-tab text & code editor with lightweight syntax highlighting, find/replace, word wrap, and font zoom.
- **Orbit View** (`orbit-view`) — Fast image viewer with folder slideshow, zoom, rotation, fullscreen, drag-and-drop, and metadata inspector.
- **Orbit Launch** (`orbit-launch`) — Keyboard-first `.desktop` app launcher with fuzzy search, safe `= math` calculator, and `> command` runner.
- **Orbit Term** (`orbit-term`) — Multi-tab PTY-backed terminal emulator with ANSI colors, copy/paste, and font zoom.

Pairs with **Orbit Files** (`/home/jacob/.gemini/antigravity/scratch/orbit-files`).

## Install Launchers & Desktop Entries

```bash
./install-suite.sh
```

To also set Orbit Files, Orbit Edit, and Orbit View as your default XDG handlers:

```bash
./install-suite.sh --set-defaults
```
