# Orbit Files

A fast, native **GTK 4 + Libadwaita** file manager written in Python, inspired by **COSMIC Files** and **Thunar**.

## Features

- **Tabs & Split View (Dual Pane)**: Open multiple tabs (`Ctrl+T`) and toggle side-by-side dual-pane browsing (`F3`, switch active pane with `F6`).
- **Sidebar**: Quick access to **Places** (Home, XDG folders, Trash, File System), **Bookmarks** (synced with `~/.config/gtk-3.0/bookmarks`), and **Mounted Drives** (live `Gio.VolumeMonitor` with eject/unmount).
- **List & Icon Grid Views**: Switch between sortable `Gtk.ColumnView` (`Ctrl+1`) and `Gtk.GridView` (`Ctrl+2`), folders-first sorting, and hidden-files toggle (`Ctrl+H`).
- **Breadcrumb Path Bar + Location Entry**: Clickable path breadcrumbs with `Ctrl+L` editable location entry (`~` and `trash:///` supported).
- **Full File Operations**: Copy, cut, paste, rename (`F2`), new folder (`Ctrl+Shift+N`), new file, move to Trash (`Delete`), restore from Trash, permanent delete (`Shift+Delete`), Properties (`Alt+Enter`), drag-and-drop between panes/folders/sidebar, and right-click context menus.
- **Quick Search / Filter & Preview Pane**: Instant live folder filter (`Ctrl+F`) and collapsible inspector/preview drawer (`F4`) for images, text/code snippets, folders, and metadata.
- **Live Directory Watching**: Automatically refreshes when files are added, renamed, or removed externally.

## Running

```bash
cd /home/jacob/.gemini/antigravity/scratch/orbit-files
python3 -m orbit_files
```

You can also pass a starting directory:

```bash
python3 -m orbit_files ~/Documents
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+T` / `Ctrl+W` | New Tab / Close Tab |
| `F3` / `F6` | Toggle Split View / Switch Active Pane |
| `F4` or `Ctrl+I` | Toggle Preview Pane |
| `F9` | Toggle Sidebar |
| `Ctrl+1` / `Ctrl+2` | List View / Grid View |
| `Ctrl+H` | Show / Hide Hidden Files |
| `Ctrl+L` | Focus Path / Location Bar |
| `Ctrl+F` | Filter Current Folder |
| `Alt+Left` / `Alt+Right` / `Alt+Up` | Back / Forward / Parent Folder |
| `F2` | Rename Selected Item |
| `Ctrl+Shift+N` | New Folder |
| `Ctrl+C` / `Ctrl+X` / `Ctrl+V` | Copy / Cut / Paste |
| `Delete` / `Shift+Delete` | Move to Trash / Delete Permanently |
| `Alt+Enter` | Properties |
| `Ctrl+D` | Bookmark Current Folder |
| `F5` or `Ctrl+R` | Refresh |
