"""Main application window with Tabs, Split View, Sidebar, Preview Pane, and Actions."""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

from orbit_files import APP_NAME, __version__, dialogs, file_ops
from orbit_files.models import format_size, query_file_item
from orbit_files.pane import FilePane
from orbit_files.preview import PreviewPane
from orbit_files.sidebar import PlacesSidebar


class TabWorkspace(Gtk.Box):
    """Holds one or two (split view) FilePanes inside a single browser tab."""

    __gsignals__ = {
        "state-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "open-in-new-tab": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "notify-message": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(
        self,
        initial_dir: Gio.File | None = None,
        show_hidden: bool = False,
        view_mode: str = "list",
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self._show_hidden = show_hidden
        self._view_mode = view_mode
        self._paned: Gtk.Paned | None = None
        self.secondary_pane: FilePane | None = None

        self.primary_pane = self._create_pane(initial_dir)
        self.active_pane: FilePane = self.primary_pane
        self.append(self.primary_pane)

    def _create_pane(self, initial_dir: Gio.File | None) -> FilePane:
        pane = FilePane(
            initial_dir=initial_dir,
            show_hidden=self._show_hidden,
            view_mode=self._view_mode,
        )
        pane.connect("activated-pane", lambda p: self.set_active_pane(p))
        pane.connect("location-changed", lambda _p: self.emit("state-changed"))
        pane.connect("selection-changed", lambda _p: self.emit("state-changed"))
        pane.connect("open-in-new-tab", lambda _p, gfile: self.emit("open-in-new-tab", gfile))
        pane.connect("notify-message", lambda _p, msg: self.emit("notify-message", msg))
        return pane

    @property
    def is_split(self) -> bool:
        return self.secondary_pane is not None

    def panes(self) -> list[FilePane]:
        result = [self.primary_pane]
        if self.secondary_pane is not None:
            result.append(self.secondary_pane)
        return result

    def set_active_pane(self, pane: FilePane) -> None:
        if pane not in self.panes():
            return
        self.active_pane = pane
        self._update_active_styles()
        self.emit("state-changed")

    def toggle_active_pane(self) -> None:
        if self.secondary_pane is None:
            return
        next_pane = (
            self.secondary_pane
            if self.active_pane is self.primary_pane
            else self.primary_pane
        )
        self.set_active_pane(next_pane)

    def _update_active_styles(self) -> None:
        if not self.is_split:
            self.primary_pane.set_active_style(False)
            return
        for pane in self.panes():
            pane.set_active_style(pane is self.active_pane)

    def set_split(self, enabled: bool) -> None:
        if enabled == self.is_split:
            return

        if enabled:
            self.remove(self.primary_pane)
            self.secondary_pane = self._create_pane(self.primary_pane.current_dir)
            self._paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
            self._paned.set_hexpand(True)
            self._paned.set_vexpand(True)
            self._paned.set_wide_handle(True)
            self._paned.set_resize_start_child(True)
            self._paned.set_resize_end_child(True)
            self._paned.set_shrink_start_child(False)
            self._paned.set_shrink_end_child(False)
            self._paned.set_start_child(self.primary_pane)
            self._paned.set_end_child(self.secondary_pane)
            self.append(self._paned)
            self.active_pane = self.secondary_pane
        else:
            assert self._paned is not None and self.secondary_pane is not None
            keep_pane = self.active_pane
            other_pane = (
                self.secondary_pane
                if keep_pane is self.primary_pane
                else self.primary_pane
            )
            other_pane.cleanup()
            self._paned.set_start_child(None)
            self._paned.set_end_child(None)
            self.remove(self._paned)
            self._paned = None
            self.primary_pane = keep_pane
            self.secondary_pane = None
            self.active_pane = self.primary_pane
            self.append(self.primary_pane)

        self._update_active_styles()
        self.emit("state-changed")

    def set_show_hidden(self, show: bool) -> None:
        self._show_hidden = show
        for pane in self.panes():
            pane.set_show_hidden(show)

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        for pane in self.panes():
            pane.set_view_mode(mode)

    def cleanup(self) -> None:
        for pane in self.panes():
            pane.cleanup()


class MainWindow(Adw.ApplicationWindow):
    """Primary Orbit Files window."""

    def __init__(self, app: Adw.Application, initial_dir: Gio.File | None = None) -> None:
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(1160, 740)

        self.clipboard = file_ops.FileClipboard()
        self._show_hidden = False
        self._view_mode = "list"

        self._setup_actions()
        self._build_ui()
        self.add_tab(initial_dir or Gio.File.new_for_path(str(Path.home())))

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        self._split_view = Adw.OverlaySplitView()
        self._split_view.set_min_sidebar_width(210)
        self._split_view.set_max_sidebar_width(280)
        self._split_view.set_sidebar_width_fraction(0.20)
        self._toast_overlay.set_child(self._split_view)

        # Left sidebar
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_end_title_buttons(False)
        sidebar_title = Gtk.Label(label=APP_NAME)
        sidebar_title.add_css_class("title")
        sidebar_header.set_title_widget(sidebar_title)
        sidebar_toolbar.add_top_bar(sidebar_header)

        self._sidebar = PlacesSidebar(
            on_navigate=self._on_sidebar_navigate,
            on_drop_files=self._on_sidebar_drop_files,
            on_notify=self.show_toast,
        )
        sidebar_toolbar.set_content(self._sidebar)
        self._split_view.set_sidebar(sidebar_toolbar)

        # Main content area
        content_toolbar = Adw.ToolbarView()
        self._split_view.set_content(content_toolbar)

        # Top HeaderBar
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)

        # Left navigation controls
        self._sidebar_btn = Gtk.ToggleButton()
        self._sidebar_btn.set_icon_name("sidebar-show-symbolic")
        self._sidebar_btn.set_active(True)
        self._sidebar_btn.set_tooltip_text("Toggle Sidebar (F9)")
        self._sidebar_btn.bind_property(
            "active",
            self._split_view,
            "show-sidebar",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        header.pack_start(self._sidebar_btn)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.add_css_class("linked")

        self._back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._back_btn.set_tooltip_text("Back (Alt+Left)")
        self._back_btn.set_action_name("win.go-back")
        nav_box.append(self._back_btn)

        self._forward_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self._forward_btn.set_tooltip_text("Forward (Alt+Right)")
        self._forward_btn.set_action_name("win.go-forward")
        nav_box.append(self._forward_btn)

        self._up_btn = Gtk.Button.new_from_icon_name("go-up-symbolic")
        self._up_btn.set_tooltip_text("Parent Folder (Alt+Up)")
        self._up_btn.set_action_name("win.go-up")
        nav_box.append(self._up_btn)
        header.pack_start(nav_box)

        # Center view switcher (List / Grid)
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        view_box.add_css_class("linked")

        self._list_btn = Gtk.ToggleButton()
        self._list_btn.set_icon_name("view-list-symbolic")
        self._list_btn.set_tooltip_text("List View (Ctrl+1)")
        self._list_btn.set_active(True)
        self._list_btn.connect("toggled", self._on_list_btn_toggled)
        view_box.append(self._list_btn)

        self._grid_btn = Gtk.ToggleButton()
        self._grid_btn.set_icon_name("view-grid-symbolic")
        self._grid_btn.set_tooltip_text("Icon Grid View (Ctrl+2)")
        self._grid_btn.set_group(self._list_btn)
        self._grid_btn.connect("toggled", self._on_grid_btn_toggled)
        view_box.append(self._grid_btn)
        header.set_title_widget(view_box)

        # Right controls: Menu, Preview, Split, Search, New Tab
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text("Main Menu")
        menu_btn.set_menu_model(self._build_primary_menu())
        header.pack_end(menu_btn)

        self._preview_btn = Gtk.ToggleButton()
        self._preview_btn.set_icon_name("view-reveal-symbolic")
        self._preview_btn.set_tooltip_text("Toggle Preview Pane (F4)")
        self._preview_btn.connect("toggled", self._on_preview_toggled)
        header.pack_end(self._preview_btn)

        self._split_btn = Gtk.ToggleButton()
        self._split_btn.set_icon_name("view-dual-symbolic")
        self._split_btn.set_tooltip_text("Toggle Split View (F3)")
        self._split_btn.connect("toggled", self._on_split_toggled)
        header.pack_end(self._split_btn)

        search_btn = Gtk.Button.new_from_icon_name("system-search-symbolic")
        search_btn.set_tooltip_text("Filter Current Folder (Ctrl+F)")
        search_btn.set_action_name("win.toggle-search")
        header.pack_end(search_btn)

        new_tab_btn = Gtk.Button.new_from_icon_name("tab-new-symbolic")
        new_tab_btn.set_tooltip_text("New Tab (Ctrl+T)")
        new_tab_btn.set_action_name("win.new-tab")
        header.pack_end(new_tab_btn)

        content_toolbar.add_top_bar(header)

        # Tab bar (auto-hides when only 1 tab is open)
        self._tab_view = Adw.TabView()
        self._tab_view.set_hexpand(True)
        self._tab_view.set_vexpand(True)
        self._tab_view.connect("notify::selected-page", self._on_tab_selected)
        self._tab_view.connect("close-page", self._on_close_page)

        self._tab_bar = Adw.TabBar()
        self._tab_bar.set_view(self._tab_view)
        self._tab_bar.set_autohide(True)
        self._tab_bar.set_expand_tabs(False)
        content_toolbar.add_top_bar(self._tab_bar)

        # Main workspace + collapsible right preview pane
        body_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body_box.set_hexpand(True)
        body_box.set_vexpand(True)
        body_box.append(self._tab_view)

        self._preview_revealer = Gtk.Revealer()
        self._preview_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self._preview_revealer.set_transition_duration(180)
        self._preview_revealer.set_reveal_child(False)

        preview_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        preview_wrapper.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self._preview_pane = PreviewPane()
        preview_wrapper.append(self._preview_pane)
        self._preview_revealer.set_child(preview_wrapper)
        body_box.append(self._preview_revealer)

        content_toolbar.set_content(body_box)

        # Bottom Status Bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.add_css_class("orbit-statusbar")
        status_bar.set_margin_top(4)
        status_bar.set_margin_bottom(4)
        status_bar.set_margin_start(12)
        status_bar.set_margin_end(12)

        self._status_left = Gtk.Label(label="")
        self._status_left.set_xalign(0.0)
        self._status_left.set_hexpand(True)
        self._status_left.add_css_class("caption")
        self._status_left.add_css_class("dim-label")
        status_bar.append(self._status_left)

        self._status_right = Gtk.Label(label="")
        self._status_right.set_xalign(1.0)
        self._status_right.add_css_class("caption")
        self._status_right.add_css_class("dim-label")
        status_bar.append(self._status_right)

        content_toolbar.add_bottom_bar(status_bar)

    def _build_primary_menu(self) -> Gio.Menu:
        menu = Gio.Menu()

        create_sec = Gio.Menu()
        create_sec.append("New Folder…", "win.new-folder")
        create_sec.append("New File…", "win.new-file")
        create_sec.append("Open Terminal Here", "win.open-terminal")
        menu.append_section(None, create_sec)

        view_sec = Gio.Menu()
        view_sec.append("Show Hidden Files", "win.toggle-hidden")
        view_sec.append("Bookmark Current Folder", "win.bookmark-current")
        view_sec.append("Refresh", "win.refresh")
        menu.append_section(None, view_sec)

        app_sec = Gio.Menu()
        app_sec.append("About Orbit Files", "win.about")
        menu.append_section(None, app_sec)
        return menu

    # ------------------------------------------------------------------
    # Tab & Pane Helpers
    # ------------------------------------------------------------------

    def add_tab(self, initial_dir: Gio.File | None = None) -> TabWorkspace:
        workspace = TabWorkspace(
            initial_dir=initial_dir,
            show_hidden=self._show_hidden,
            view_mode=self._view_mode,
        )
        workspace.connect("state-changed", lambda _ws: self._sync_ui_from_active())
        workspace.connect("open-in-new-tab", lambda _ws, gfile: self.add_tab(gfile))
        workspace.connect("notify-message", lambda _ws, msg: self.show_toast(msg))

        page = self._tab_view.append(workspace)
        page.set_title(workspace.active_pane.display_title)
        self._tab_view.set_selected_page(page)
        self._sync_ui_from_active()
        return workspace

    @property
    def active_workspace(self) -> TabWorkspace | None:
        page = self._tab_view.get_selected_page()
        if page is None:
            return None
        child = page.get_child()
        return child if isinstance(child, TabWorkspace) else None

    @property
    def active_pane(self) -> FilePane | None:
        ws = self.active_workspace
        return ws.active_pane if ws is not None else None

    def _on_tab_selected(self, _tv: Adw.TabView, _pspec: GObject.ParamSpec) -> None:
        self._sync_ui_from_active()

    def _on_close_page(self, _tv: Adw.TabView, page: Adw.TabPage) -> bool:
        child = page.get_child()
        if isinstance(child, TabWorkspace):
            child.cleanup()
        if self._tab_view.get_n_pages() <= 1:
            self._tab_view.close_page_finish(page, True)
            self.close()
            return True
        self._tab_view.close_page_finish(page, True)
        return True

    def _sync_ui_from_active(self) -> None:
        ws = self.active_workspace
        if ws is None:
            return
        pane = ws.active_pane

        # Update tab title
        page = self._tab_view.get_selected_page()
        if page is not None:
            title = pane.display_title
            if ws.is_split:
                title = f"{ws.primary_pane.display_title} | {ws.secondary_pane.display_title}"  # type: ignore[union-attr]
            page.set_title(title)

        # Update nav buttons
        self._back_btn.set_sensitive(pane.can_go_back)
        self._forward_btn.set_sensitive(pane.can_go_forward)
        self._up_btn.set_sensitive(pane.can_go_up)

        # Sync split toggle button without re-triggering
        if self._split_btn.get_active() != ws.is_split:
            self._split_btn.set_active(ws.is_split)

        # Highlight sidebar
        self._sidebar.highlight_location(pane.current_dir)

        # Update preview pane & status bar
        selected = pane.get_selected_items()
        if self._preview_revealer.get_reveal_child():
            self._preview_pane.show_items(selected)

        visible_count = pane.total_visible_items
        noun = "item" if visible_count == 1 else "items"
        if selected:
            sel_size = sum(i.size for i in selected if not i.is_dir)
            sel_files = sum(1 for i in selected if not i.is_dir)
            size_part = f" ({format_size(sel_size)})" if sel_files else ""
            self._status_left.set_text(
                f"{visible_count} {noun}  •  {len(selected)} selected{size_part}"
            )
        else:
            self._status_left.set_text(f"{visible_count} {noun}")

        if ws.is_split:
            side = "Left Pane" if pane is ws.primary_pane else "Right Pane"
            self._status_right.set_text(f"Split View: {side} (F6 to switch)")
        else:
            self._status_right.set_text(pane.current_dir.get_path() or pane.current_dir.get_uri())

    def show_toast(self, message: str) -> None:
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self._toast_overlay.add_toast(toast)

    # ------------------------------------------------------------------
    # Toolbar & Sidebar Callbacks
    # ------------------------------------------------------------------

    def _on_sidebar_navigate(self, gfile: Gio.File) -> None:
        pane = self.active_pane
        if pane is not None:
            pane.navigate_to(gfile)

    def _on_sidebar_drop_files(
        self, sources: list[Gio.File], dest_dir: Gio.File, is_copy: bool
    ) -> None:
        def _done(ok: bool, msg: str) -> None:
            self.show_toast(msg if ok else f"Error: {msg}")
            if self.active_pane:
                self.active_pane.refresh()

        if is_copy:
            file_ops.copy_files(sources, dest_dir, on_complete=_done)
        else:
            file_ops.move_files(sources, dest_dir, on_complete=_done)

    def _on_list_btn_toggled(self, btn: Gtk.ToggleButton) -> None:
        if btn.get_active():
            self._set_view_mode("list")

    def _on_grid_btn_toggled(self, btn: Gtk.ToggleButton) -> None:
        if btn.get_active():
            self._set_view_mode("grid")

    def _set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        for idx in range(self._tab_view.get_n_pages()):
            ws = self._tab_view.get_nth_page(idx).get_child()
            if isinstance(ws, TabWorkspace):
                ws.set_view_mode(mode)

    def _on_split_toggled(self, btn: Gtk.ToggleButton) -> None:
        ws = self.active_workspace
        if ws is not None:
            ws.set_split(btn.get_active())

    def _on_preview_toggled(self, btn: Gtk.ToggleButton) -> None:
        reveal = btn.get_active()
        self._preview_revealer.set_reveal_child(reveal)
        if reveal and self.active_pane is not None:
            self._preview_pane.show_items(self.active_pane.get_selected_items())

    # ------------------------------------------------------------------
    # Window Actions
    # ------------------------------------------------------------------

    def _setup_actions(self) -> None:
        simple_actions = [
            ("new-tab", self._act_new_tab),
            ("close-tab", self._act_close_tab),
            ("toggle-split", self._act_toggle_split),
            ("switch-pane", self._act_switch_pane),
            ("toggle-preview", self._act_toggle_preview),
            ("toggle-sidebar", self._act_toggle_sidebar),
            ("toggle-search", self._act_toggle_search),
            ("focus-location", self._act_focus_location),
            ("view-list", lambda *_: self._list_btn.set_active(True)),
            ("view-grid", lambda *_: self._grid_btn.set_active(True)),
            ("go-back", lambda *_: self.active_pane and self.active_pane.go_back()),
            ("go-forward", lambda *_: self.active_pane and self.active_pane.go_forward()),
            ("go-up", lambda *_: self.active_pane and self.active_pane.go_up()),
            ("refresh", lambda *_: self.active_pane and self.active_pane.refresh()),
            ("select-all", lambda *_: self.active_pane and self.active_pane.select_all()),
            ("open-selected", self._act_open_selected),
            ("open-in-new-tab", self._act_open_in_new_tab),
            ("cut", self._act_cut),
            ("copy", self._act_copy),
            ("paste", self._act_paste),
            ("rename", self._act_rename),
            ("trash", self._act_trash),
            ("restore-trash", self._act_restore_trash),
            ("delete-permanent", self._act_delete_permanent),
            ("new-folder", self._act_new_folder),
            ("new-file", self._act_new_file),
            ("properties", self._act_properties),
            ("bookmark-current", self._act_bookmark_current),
            ("bookmark-selected", self._act_bookmark_selected),
            ("open-terminal", lambda *_: self.active_pane and self.active_pane.open_terminal_here()),
            ("about", self._act_about),
        ]
        for name, cb in simple_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", cb)
            self.add_action(action)

        # Stateful toggle for hidden files
        hidden_action = Gio.SimpleAction.new_stateful(
            "toggle-hidden", None, GLib.Variant.new_boolean(False)
        )
        hidden_action.connect("change-state", self._act_toggle_hidden)
        self.add_action(hidden_action)

    def _act_new_tab(self, *_args: object) -> None:
        start_dir = self.active_pane.current_dir if self.active_pane else None
        self.add_tab(start_dir)

    def _act_close_tab(self, *_args: object) -> None:
        page = self._tab_view.get_selected_page()
        if page is not None:
            self._tab_view.close_page(page)

    def _act_toggle_split(self, *_args: object) -> None:
        self._split_btn.set_active(not self._split_btn.get_active())

    def _act_switch_pane(self, *_args: object) -> None:
        if self.active_workspace is not None:
            self.active_workspace.toggle_active_pane()

    def _act_toggle_preview(self, *_args: object) -> None:
        self._preview_btn.set_active(not self._preview_btn.get_active())

    def _act_toggle_sidebar(self, *_args: object) -> None:
        self._sidebar_btn.set_active(not self._sidebar_btn.get_active())

    def _act_toggle_search(self, *_args: object) -> None:
        if self.active_pane is not None:
            self.active_pane.toggle_search()

    def _act_focus_location(self, *_args: object) -> None:
        if self.active_pane is not None:
            self.active_pane.focus_location_bar()

    def _act_toggle_hidden(self, action: Gio.SimpleAction, value: GLib.Variant) -> None:
        show = value.get_boolean()
        action.set_state(value)
        self._show_hidden = show
        for idx in range(self._tab_view.get_n_pages()):
            ws = self._tab_view.get_nth_page(idx).get_child()
            if isinstance(ws, TabWorkspace):
                ws.set_show_hidden(show)
        self._sync_ui_from_active()

    def _act_open_selected(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        for item in pane.get_selected_items():
            pane.open_item(item)
            if item.is_dir:
                break

    def _act_open_in_new_tab(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        for item in pane.get_selected_items():
            if item.is_dir:
                self.add_tab(item.gfile)

    def _act_cut(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return
        items = pane.get_selected_items()
        if not items:
            return
        self.clipboard.set_files([i.gfile for i in items], is_cut=True)
        noun = "item" if len(items) == 1 else "items"
        self.show_toast(f"Cut {len(items)} {noun}")

    def _act_copy(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return
        items = pane.get_selected_items()
        if not items:
            return
        self.clipboard.set_files([i.gfile for i in items], is_cut=False)
        noun = "item" if len(items) == 1 else "items"
        self.show_toast(f"Copied {len(items)} {noun} to clipboard")

    def _act_paste(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash or not self.clipboard.has_files:
            return
        sources = self.clipboard.get_gfiles()
        dest = pane.current_dir
        is_cut = self.clipboard.is_cut

        def _done(ok: bool, msg: str) -> None:
            if ok and is_cut:
                self.clipboard.clear()
            self.show_toast(msg if ok else f"Error: {msg}")
            pane.refresh()

        if is_cut:
            file_ops.move_files(sources, dest, on_complete=_done)
        else:
            file_ops.copy_files(sources, dest, on_complete=_done)

    def _act_rename(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return
        items = pane.get_selected_items()
        if len(items) != 1:
            return
        item = items[0]

        def _do_rename(new_name: str) -> None:
            if new_name.strip() == item.name:
                return
            try:
                file_ops.rename_file(item.gfile, new_name)
                pane.refresh()
                self.show_toast(f"Renamed to “{new_name.strip()}”")
            except Exception as exc:
                self.show_toast(f"Rename failed: {exc}")

        dialogs.prompt_text_dialog(
            parent=self,
            heading="Rename Item",
            body=f"Enter a new name for “{item.name}”:",
            initial_text=item.name,
            confirm_label="Rename",
            on_confirm=_do_rename,
            select_stem=not item.is_dir,
        )

    def _act_trash(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        items = pane.get_selected_items()
        if not items:
            return
        if pane.is_trash:
            self._act_delete_permanent()
            return

        def _done(ok: bool, msg: str) -> None:
            self.show_toast(msg if ok else f"Error: {msg}")
            pane.refresh()

        file_ops.trash_files([i.gfile for i in items], on_complete=_done)

    def _act_restore_trash(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or not pane.is_trash:
            return
        items = pane.get_selected_items()
        if not items:
            return

        def _done(ok: bool, msg: str) -> None:
            self.show_toast(msg if ok else f"Error: {msg}")
            pane.refresh()

        file_ops.restore_from_trash([i.gfile for i in items], on_complete=_done)

    def _act_delete_permanent(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        items = pane.get_selected_items()
        if not items:
            return

        def _confirm() -> None:
            def _done(ok: bool, msg: str) -> None:
                self.show_toast(msg if ok else f"Error: {msg}")
                pane.refresh()

            file_ops.delete_files_permanently([i.gfile for i in items], on_complete=_done)

        dialogs.confirm_delete_dialog(self, items, _confirm)

    def _act_new_folder(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return

        def _do_create(name: str) -> None:
            try:
                file_ops.create_folder(pane.current_dir, name)
                pane.refresh()
                self.show_toast(f"Created folder “{name.strip()}”")
            except Exception as exc:
                self.show_toast(f"Could not create folder: {exc}")

        dialogs.prompt_text_dialog(
            parent=self,
            heading="New Folder",
            body="Enter a name for the new folder:",
            initial_text="Untitled Folder",
            confirm_label="Create",
            on_confirm=_do_create,
        )

    def _act_new_file(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return

        def _do_create(name: str) -> None:
            try:
                file_ops.create_empty_file(pane.current_dir, name)
                pane.refresh()
                self.show_toast(f"Created file “{name.strip()}”")
            except Exception as exc:
                self.show_toast(f"Could not create file: {exc}")

        dialogs.prompt_text_dialog(
            parent=self,
            heading="New File",
            body="Enter a name for the new file:",
            initial_text="untitled.txt",
            confirm_label="Create",
            on_confirm=_do_create,
            select_stem=True,
        )

    def _act_properties(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        items = pane.get_selected_items()
        if items:
            dialogs.show_properties_dialog(self, items[0])
        else:
            cur_item = query_file_item(pane.current_dir)
            if cur_item is not None:
                dialogs.show_properties_dialog(self, cur_item)

    def _act_bookmark_current(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None or pane.is_trash:
            return
        added = self._sidebar.add_bookmark(pane.current_dir)
        if added:
            self.show_toast(f"Bookmarked “{pane.display_title}”")
        else:
            self.show_toast("Folder is already bookmarked")

    def _act_bookmark_selected(self, *_args: object) -> None:
        pane = self.active_pane
        if pane is None:
            return
        items = pane.get_selected_items()
        if len(items) == 1 and items[0].is_dir:
            added = self._sidebar.add_bookmark(items[0].gfile)
            if added:
                self.show_toast(f"Bookmarked “{items[0].name}”")
            else:
                self.show_toast("Folder is already bookmarked")

    def _act_about(self, *_args: object) -> None:
        about = Adw.AboutDialog()
        about.set_application_name(APP_NAME)
        about.set_version(__version__)
        about.set_application_icon("system-file-manager")
        about.set_comments(
            "A fast, native GTK 4 + Libadwaita file manager in Python, "
            "inspired by COSMIC Files and Thunar."
        )
        about.present(self)
