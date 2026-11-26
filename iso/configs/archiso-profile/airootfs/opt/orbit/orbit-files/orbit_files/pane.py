"""FilePane widget: List & Grid views, filtering, sorting, DnD, context menu, and live watching."""

from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable

from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk, Pango

from orbit_files import file_ops
from orbit_files.models import FileItem, enumerate_directory
from orbit_files.pathbar import PathBar


def _cmp_items(a: FileItem, b: FileItem, key_fn: Callable[[FileItem], object]) -> int:
    """Compare two FileItems with folders always sorted before files."""
    if a.is_dir != b.is_dir:
        return -1 if a.is_dir else 1
    va = key_fn(a)
    vb = key_fn(b)
    if va < vb:  # type: ignore[operator]
        return -1
    if va > vb:  # type: ignore[operator]
        return 1
    if a.sort_name < b.sort_name:
        return -1
    if a.sort_name > b.sort_name:
        return 1
    return 0


class FilePane(Gtk.Box):
    """A self-contained file browser pane supporting List and Grid views."""

    __gsignals__ = {
        "activated-pane": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "location-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "selection-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "open-in-new-tab": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "notify-message": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "request-action": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(
        self,
        initial_dir: Gio.File | None = None,
        show_hidden: bool = False,
        view_mode: str = "list",
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.add_css_class("file-pane")

        self._current_dir: Gio.File = initial_dir or Gio.File.new_for_path(str(Path.home()))
        self._back_stack: list[Gio.File] = []
        self._forward_stack: list[Gio.File] = []
        self._show_hidden = show_hidden
        self._filter_query = ""
        self._view_mode = view_mode
        self._load_generation = 0
        self._dir_monitor: Gio.FileMonitor | None = None
        self._refresh_timeout_id: int | None = None
        self._active_popover: Gtk.PopoverMenu | None = None
        self._is_active = False
        self._thumb_cache: dict[tuple[str, int], Gdk.Texture] = {}

        # Track focus/clicks anywhere inside the pane to mark it as active
        click_tracker = Gtk.GestureClick()
        click_tracker.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click_tracker.connect("pressed", lambda *_: self.emit("activated-pane"))
        self.add_controller(click_tracker)

        # Top path bar for this pane
        self.path_bar = PathBar(on_navigate=self.navigate_to)
        self.path_bar.set_margin_top(4)
        self.path_bar.set_margin_bottom(4)
        self.path_bar.set_margin_start(6)
        self.path_bar.set_margin_end(6)
        self.append(self.path_bar)

        # Quick search / filter bar
        self._search_bar = Gtk.SearchBar()
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_hexpand(True)
        self._search_entry.set_placeholder_text("Filter current folder…")
        self._search_entry.connect("search-changed", self._on_search_changed)
        self._search_bar.set_child(self._search_entry)
        self._search_bar.connect_entry(self._search_entry)
        self._search_bar.set_show_close_button(True)
        self.append(self._search_bar)

        # Data pipeline: ListStore -> FilterListModel -> SortListModel -> MultiSelection
        self._store = Gio.ListStore.new(FileItem)

        self._filter = Gtk.CustomFilter.new(self._filter_func)
        self._filter_model = Gtk.FilterListModel.new(self._store, self._filter)

        self._sort_model = Gtk.SortListModel.new(self._filter_model, None)
        self._selection = Gtk.MultiSelection.new(self._sort_model)
        self._selection.connect("selection-changed", self._on_selection_changed)

        # Content stack: list | grid | empty | error
        self._content_stack = Gtk.Stack()
        self._content_stack.set_hexpand(True)
        self._content_stack.set_vexpand(True)

        self._column_view = self._build_column_view()
        self._sort_model.set_sorter(self._column_view.get_sorter())

        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        list_scroll.set_child(self._column_view)
        self._attach_pane_interactions(list_scroll)
        self._content_stack.add_named(list_scroll, "list")

        self._grid_view = self._build_grid_view()
        grid_scroll = Gtk.ScrolledWindow()
        grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid_scroll.set_child(self._grid_view)
        self._attach_pane_interactions(grid_scroll)
        self._content_stack.add_named(grid_scroll, "grid")

        self._empty_page = Adw.StatusPage()
        self._empty_page.set_icon_name("folder-open-symbolic")
        self._empty_page.set_title("Folder is Empty")
        self._empty_page.set_description("Drag files here or create a new folder.")
        self._attach_pane_interactions(self._empty_page)
        self._content_stack.add_named(self._empty_page, "empty")

        self._error_page = Adw.StatusPage()
        self._error_page.set_icon_name("dialog-error-symbolic")
        self._error_page.set_title("Cannot Open Location")
        self._content_stack.add_named(self._error_page, "error")

        self.append(self._content_stack)

        # Initial load
        self.navigate_to(self._current_dir, record_history=False)

    # ------------------------------------------------------------------
    # Properties & public API
    # ------------------------------------------------------------------

    @property
    def current_dir(self) -> Gio.File:
        return self._current_dir

    @property
    def is_trash(self) -> bool:
        return self._current_dir.get_uri().startswith("trash:")

    @property
    def can_go_back(self) -> bool:
        return bool(self._back_stack)

    @property
    def can_go_forward(self) -> bool:
        return bool(self._forward_stack)

    @property
    def can_go_up(self) -> bool:
        return self._current_dir.get_parent() is not None

    @property
    def display_title(self) -> str:
        if self.is_trash:
            return "Trash"
        path_str = self._current_dir.get_path()
        if path_str:
            p = Path(path_str)
            if p == Path.home():
                return "Home"
            return p.name or "/"
        return self._current_dir.get_basename() or self._current_dir.get_uri()

    @property
    def total_visible_items(self) -> int:
        return self._sort_model.get_n_items()

    @property
    def total_items(self) -> int:
        return self._store.get_n_items()

    def set_active_style(self, active: bool) -> None:
        self._is_active = active
        if active:
            self.add_css_class("file-pane-active")
        else:
            self.remove_css_class("file-pane-active")

    def set_show_hidden(self, show: bool) -> None:
        if self._show_hidden != show:
            self._show_hidden = show
            self._filter.changed(Gtk.FilterChange.DIFFERENT)
            self._update_empty_state()
            self.emit("selection-changed")

    def set_view_mode(self, mode: str) -> None:
        if mode not in ("list", "grid"):
            return
        self._view_mode = mode
        if self._content_stack.get_visible_child_name() in ("list", "grid"):
            self._content_stack.set_visible_child_name(mode)

    def get_view_mode(self) -> str:
        return self._view_mode

    def toggle_search(self) -> None:
        active = self._search_bar.get_search_mode()
        self._search_bar.set_search_mode(not active)
        if not active:
            self._search_entry.grab_focus()
        else:
            self._search_entry.set_text("")

    def focus_location_bar(self) -> None:
        self.path_bar.focus_entry()

    def get_selected_items(self) -> list[FileItem]:
        bitset = self._selection.get_selection()
        items: list[FileItem] = []
        valid, it, pos = Gtk.BitsetIter.init_first(bitset)
        while valid:
            item = self._sort_model.get_item(pos)
            if isinstance(item, FileItem):
                items.append(item)
            valid, pos = it.next()
        return items

    def select_all(self) -> None:
        self._selection.select_all()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to(self, gfile: Gio.File, record_history: bool = True) -> None:
        if record_history and not gfile.equal(self._current_dir):
            self._back_stack.append(self._current_dir)
            self._forward_stack.clear()

        self._current_dir = gfile
        self.path_bar.set_location(gfile)

        # Clear quick filter when changing folders
        if self._filter_query:
            self._search_entry.set_text("")
            self._search_bar.set_search_mode(False)

        self._setup_monitor()
        self.refresh()
        self.emit("location-changed")

    def go_back(self) -> None:
        if not self._back_stack:
            return
        target = self._back_stack.pop()
        self._forward_stack.append(self._current_dir)
        self.navigate_to(target, record_history=False)

    def go_forward(self) -> None:
        if not self._forward_stack:
            return
        target = self._forward_stack.pop()
        self._back_stack.append(self._current_dir)
        self.navigate_to(target, record_history=False)

    def go_up(self) -> None:
        parent = self._current_dir.get_parent()
        if parent is not None:
            self.navigate_to(parent)

    def refresh(self) -> None:
        self._load_generation += 1
        gen = self._load_generation
        target = self._current_dir

        def _worker() -> None:
            try:
                items = enumerate_directory(target)
                GLib.idle_add(self._apply_directory_items, gen, items, None)
            except GLib.Error as err:
                GLib.idle_add(self._apply_directory_items, gen, [], err.message)
            except Exception as exc:
                GLib.idle_add(self._apply_directory_items, gen, [], str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_directory_items(
        self, gen: int, items: list[FileItem], error_msg: str | None
    ) -> bool:
        if gen != self._load_generation:
            return False

        if error_msg is not None:
            self._store.remove_all()
            self._error_page.set_description(error_msg)
            self._content_stack.set_visible_child_name("error")
            self.emit("selection-changed")
            return False

        self._store.splice(0, self._store.get_n_items(), items)
        self._update_empty_state()
        self.emit("selection-changed")
        return False

    def _update_empty_state(self) -> None:
        if self._content_stack.get_visible_child_name() == "error":
            return
        if self._sort_model.get_n_items() == 0:
            if self._filter_query:
                self._empty_page.set_icon_name("system-search-symbolic")
                self._empty_page.set_title("No Matching Items")
                self._empty_page.set_description(
                    f"No files or folders match “{self._filter_query}”."
                )
            elif self.is_trash:
                self._empty_page.set_icon_name("user-trash-symbolic")
                self._empty_page.set_title("Trash is Empty")
                self._empty_page.set_description("Deleted items will appear here.")
            else:
                self._empty_page.set_icon_name("folder-open-symbolic")
                self._empty_page.set_title("Folder is Empty")
                self._empty_page.set_description("Drag files here or create a new folder.")
            self._content_stack.set_visible_child_name("empty")
        else:
            self._content_stack.set_visible_child_name(self._view_mode)

    def _setup_monitor(self) -> None:
        if self._dir_monitor is not None:
            self._dir_monitor.cancel()
            self._dir_monitor = None
        try:
            self._dir_monitor = self._current_dir.monitor_directory(
                Gio.FileMonitorFlags.NONE, None
            )
            self._dir_monitor.connect("changed", self._on_dir_monitor_changed)
        except GLib.Error:
            self._dir_monitor = None

    def _on_dir_monitor_changed(
        self,
        _monitor: Gio.FileMonitor,
        _file: Gio.File,
        _other_file: Gio.File | None,
        event_type: Gio.FileMonitorEvent,
    ) -> None:
        if event_type in (
            Gio.FileMonitorEvent.CREATED,
            Gio.FileMonitorEvent.DELETED,
            Gio.FileMonitorEvent.RENAMED,
            Gio.FileMonitorEvent.MOVED_IN,
            Gio.FileMonitorEvent.MOVED_OUT,
            Gio.FileMonitorEvent.CHANGES_DONE_HINT,
        ):
            if self._refresh_timeout_id is not None:
                GLib.source_remove(self._refresh_timeout_id)
            self._refresh_timeout_id = GLib.timeout_add(180, self._debounced_refresh)

    def _debounced_refresh(self) -> bool:
        self._refresh_timeout_id = None
        self.refresh()
        return False

    def cleanup(self) -> None:
        """Release file monitors and timers when a pane or tab closes."""
        if self._refresh_timeout_id is not None:
            GLib.source_remove(self._refresh_timeout_id)
            self._refresh_timeout_id = None
        if self._dir_monitor is not None:
            self._dir_monitor.cancel()
            self._dir_monitor = None

    # ------------------------------------------------------------------
    # Filtering & Selection
    # ------------------------------------------------------------------

    def _filter_func(self, item: GObject.Object) -> bool:
        if not isinstance(item, FileItem):
            return False
        if not self._show_hidden and item.is_hidden:
            return False
        if self._filter_query and self._filter_query not in item.sort_name:
            return False
        return True

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._filter_query = entry.get_text().strip().casefold()
        self._filter.changed(Gtk.FilterChange.DIFFERENT)
        self._update_empty_state()
        self.emit("selection-changed")

    def _on_selection_changed(
        self, _model: Gtk.SelectionModel, _position: int, _n_items: int
    ) -> None:
        self.emit("selection-changed")

    # ------------------------------------------------------------------
    # List View (Gtk.ColumnView)
    # ------------------------------------------------------------------

    def _build_column_view(self) -> Gtk.ColumnView:
        cv = Gtk.ColumnView.new(self._selection)
        cv.add_css_class("data-table")
        cv.set_show_row_separators(False)
        cv.set_show_column_separators(False)
        cv.set_single_click_activate(False)
        cv.connect("activate", self._on_item_activated)

        # Name column (icon + label)
        name_factory = Gtk.SignalListItemFactory()
        name_factory.connect("setup", self._setup_name_cell)
        name_factory.connect("bind", self._bind_name_cell)
        name_col = Gtk.ColumnViewColumn.new("Name", name_factory)
        name_col.set_expand(True)
        name_col.set_resizable(True)
        name_col.set_sorter(Gtk.CustomSorter.new(lambda a, b, *_: _cmp_items(a, b, lambda x: x.sort_name)))
        cv.append_column(name_col)

        # Size column
        size_factory = Gtk.SignalListItemFactory()
        size_factory.connect("setup", lambda _f, li: self._setup_text_cell(li, xalign=1.0, dim=True))
        size_factory.connect("bind", lambda _f, li: self._bind_text_cell(li, "size_display"))
        size_col = Gtk.ColumnViewColumn.new("Size", size_factory)
        size_col.set_fixed_width(100)
        size_col.set_resizable(True)
        size_col.set_sorter(Gtk.CustomSorter.new(lambda a, b, *_: _cmp_items(a, b, lambda x: x.size)))
        cv.append_column(size_col)

        # Type column
        type_factory = Gtk.SignalListItemFactory()
        type_factory.connect("setup", lambda _f, li: self._setup_text_cell(li, xalign=0.0, dim=True))
        type_factory.connect("bind", lambda _f, li: self._bind_text_cell(li, "type_display"))
        type_col = Gtk.ColumnViewColumn.new("Type", type_factory)
        type_col.set_fixed_width(170)
        type_col.set_resizable(True)
        type_col.set_sorter(
            Gtk.CustomSorter.new(lambda a, b, *_: _cmp_items(a, b, lambda x: x.type_display.casefold()))
        )
        cv.append_column(type_col)

        # Modified column
        mtime_factory = Gtk.SignalListItemFactory()
        mtime_factory.connect("setup", lambda _f, li: self._setup_text_cell(li, xalign=0.0, dim=True))
        mtime_factory.connect("bind", lambda _f, li: self._bind_text_cell(li, "mtime_display"))
        mtime_col = Gtk.ColumnViewColumn.new("Modified", mtime_factory)
        mtime_col.set_fixed_width(150)
        mtime_col.set_resizable(True)
        mtime_col.set_sorter(Gtk.CustomSorter.new(lambda a, b, *_: _cmp_items(a, b, lambda x: x.mtime)))
        cv.append_column(mtime_col)

        cv.sort_by_column(name_col, Gtk.SortType.ASCENDING)
        return cv

    def _setup_name_cell(self, _factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(3)
        box.set_margin_bottom(3)

        icon = Gtk.Image()
        icon.set_pixel_size(20)
        box.append(icon)

        label = Gtk.Label()
        label.set_xalign(0.0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_hexpand(True)
        box.append(label)

        box._orbit_icon = icon  # type: ignore[attr-defined]
        box._orbit_label = label  # type: ignore[attr-defined]
        self._attach_item_controllers(box, list_item)
        list_item.set_child(box)

    def _bind_name_cell(self, _factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        box = list_item.get_child()
        item = list_item.get_item()
        if not isinstance(item, FileItem) or box is None:
            return
        box._orbit_icon.set_from_gicon(item.gicon)  # type: ignore[attr-defined]
        box._orbit_label.set_text(item.name)  # type: ignore[attr-defined]
        box.set_opacity(0.6 if item.is_hidden else 1.0)

    def _setup_text_cell(
        self, list_item: Gtk.ListItem, xalign: float = 0.0, dim: bool = False
    ) -> None:
        label = Gtk.Label()
        label.set_xalign(xalign)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        if dim:
            label.add_css_class("dim-label")
        self._attach_item_controllers(label, list_item)
        list_item.set_child(label)

    def _bind_text_cell(self, list_item: Gtk.ListItem, attr: str) -> None:
        label = list_item.get_child()
        item = list_item.get_item()
        if isinstance(label, Gtk.Label) and isinstance(item, FileItem):
            label.set_text(getattr(item, attr, ""))

    # ------------------------------------------------------------------
    # Grid View (Gtk.GridView)
    # ------------------------------------------------------------------

    def _build_grid_view(self) -> Gtk.GridView:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_grid_cell)
        factory.connect("bind", self._bind_grid_cell)

        gv = Gtk.GridView.new(self._selection, factory)
        gv.set_min_columns(2)
        gv.set_max_columns(12)
        gv.set_single_click_activate(False)
        gv.add_css_class("orbit-grid-view")
        gv.connect("activate", self._on_item_activated)
        return gv

    def _setup_grid_cell(self, _factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_size_request(104, 96)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.START)

        icon = Gtk.Image()
        icon.set_pixel_size(48)
        box.append(icon)

        label = Gtk.Label()
        label.set_justify(Gtk.Justification.CENTER)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_lines(2)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(14)
        box.append(label)

        box._orbit_icon = icon  # type: ignore[attr-defined]
        box._orbit_label = label  # type: ignore[attr-defined]
        self._attach_item_controllers(box, list_item)
        list_item.set_child(box)

    def _bind_grid_cell(self, _factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        box = list_item.get_child()
        item = list_item.get_item()
        if not isinstance(item, FileItem) or box is None:
            return
        icon: Gtk.Image = box._orbit_icon  # type: ignore[attr-defined]
        box._orbit_label.set_text(item.name)  # type: ignore[attr-defined]
        box.set_opacity(0.6 if item.is_hidden else 1.0)

        if item.is_image and item.path and item.size <= 15 * 1024 * 1024:
            key = (item.path, item.mtime)
            cached = self._thumb_cache.get(key)
            if cached is not None:
                icon.set_from_paintable(cached)
                return
            icon.set_from_gicon(item.gicon)
            self._load_grid_thumb_async(list_item, item, key)
        else:
            icon.set_from_gicon(item.gicon)

    def _load_grid_thumb_async(
        self, list_item: Gtk.ListItem, item: FileItem, key: tuple[str, int]
    ) -> None:
        def _worker() -> None:
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(key[0], 64, 64, True)
                tex = Gdk.Texture.new_for_pixbuf(pb)
                GLib.idle_add(self._apply_grid_thumb, list_item, item, key, tex)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_grid_thumb(
        self,
        list_item: Gtk.ListItem,
        item: FileItem,
        key: tuple[str, int],
        tex: Gdk.Texture,
    ) -> bool:
        if len(self._thumb_cache) > 300:
            self._thumb_cache.clear()
        self._thumb_cache[key] = tex
        if list_item.get_item() is item:
            box = list_item.get_child()
            if box is not None and hasattr(box, "_orbit_icon"):
                box._orbit_icon.set_from_paintable(tex)
        return False

    # ------------------------------------------------------------------
    # Item activation, Drag & Drop, Context Menus
    # ------------------------------------------------------------------

    def _on_item_activated(self, _view: Gtk.Widget, position: int) -> None:
        item = self._sort_model.get_item(position)
        if not isinstance(item, FileItem):
            return
        self.open_item(item)

    def open_item(self, item: FileItem) -> None:
        if item.is_dir:
            self.navigate_to(item.gfile)
        else:
            self._launch_file(item.gfile)

    def _launch_file(self, gfile: Gio.File) -> None:
        path_str = gfile.get_path()
        if path_str and path_str.endswith(".desktop"):
            app_info = Gio.DesktopAppInfo.new_from_filename(path_str)
            if app_info is not None:
                try:
                    app_info.launch([], None)
                    return
                except GLib.Error as err:
                    self.emit("notify-message", f"Could not launch app: {err.message}")
                    return
        try:
            Gio.AppInfo.launch_default_for_uri(gfile.get_uri(), None)
        except GLib.Error as err:
            self.emit("notify-message", f"Could not open file: {err.message}")

    def _attach_item_controllers(self, widget: Gtk.Widget, list_item: Gtk.ListItem) -> None:
        # Right-click context menu on item
        right_click = Gtk.GestureClick()
        right_click.set_button(3)

        def _on_right_click(
            gesture: Gtk.GestureClick, _n_press: int, x: float, y: float
        ) -> None:
            pos = list_item.get_position()
            if pos != Gtk.INVALID_LIST_POSITION and not self._selection.is_selected(pos):
                self._selection.select_item(pos, True)
            self.emit("activated-pane")
            self._show_context_menu(widget, x, y, on_selection=True)
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

        right_click.connect("pressed", _on_right_click)
        widget.add_controller(right_click)

        # Drag source
        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE | Gdk.DragAction.COPY)

        def _on_drag_prepare(
            _src: Gtk.DragSource, _x: float, _y: float
        ) -> Gdk.ContentProvider | None:
            item = list_item.get_item()
            if not isinstance(item, FileItem):
                return None
            pos = list_item.get_position()
            if pos != Gtk.INVALID_LIST_POSITION and self._selection.is_selected(pos):
                gfiles = [i.gfile for i in self.get_selected_items()]
            else:
                gfiles = [item.gfile]
            if not gfiles:
                return None
            file_list = Gdk.FileList.new_from_list(gfiles)
            return Gdk.ContentProvider.new_for_value(file_list)

        drag_source.connect("prepare", _on_drag_prepare)
        widget.add_controller(drag_source)

        # Drop target onto folders
        drop_target = Gtk.DropTarget.new(
            Gdk.FileList, Gdk.DragAction.MOVE | Gdk.DragAction.COPY
        )

        def _on_drop(
            dt: Gtk.DropTarget, value: object, _x: float, _y: float
        ) -> bool:
            item = list_item.get_item()
            if not isinstance(item, FileItem) or not item.is_dir:
                return False
            if isinstance(value, Gdk.FileList):
                files = list(value.get_files())
                if files:
                    action = dt.get_current_drop().get_actions() if dt.get_current_drop() else Gdk.DragAction.MOVE
                    is_copy = bool(action & Gdk.DragAction.COPY) and not bool(action & Gdk.DragAction.MOVE)
                    self._handle_drop(files, item.gfile, is_copy)
                    return True
            return False

        drop_target.connect("drop", _on_drop)
        widget.add_controller(drop_target)

    def _attach_pane_interactions(self, widget: Gtk.Widget) -> None:
        # Right-click on empty pane background
        right_click = Gtk.GestureClick()
        right_click.set_button(3)

        def _on_bg_right_click(
            _gesture: Gtk.GestureClick, _n_press: int, x: float, y: float
        ) -> None:
            self.emit("activated-pane")
            self._show_context_menu(widget, x, y, on_selection=False)

        right_click.connect("pressed", _on_bg_right_click)
        widget.add_controller(right_click)

        # Drop target onto the pane's current directory
        drop_target = Gtk.DropTarget.new(
            Gdk.FileList, Gdk.DragAction.MOVE | Gdk.DragAction.COPY
        )

        def _on_pane_drop(
            dt: Gtk.DropTarget, value: object, _x: float, _y: float
        ) -> bool:
            if isinstance(value, Gdk.FileList):
                files = list(value.get_files())
                if files:
                    action = dt.get_current_drop().get_actions() if dt.get_current_drop() else Gdk.DragAction.MOVE
                    is_copy = bool(action & Gdk.DragAction.COPY) and not bool(action & Gdk.DragAction.MOVE)
                    self._handle_drop(files, self._current_dir, is_copy)
                    return True
            return False

        drop_target.connect("drop", _on_pane_drop)
        widget.add_controller(drop_target)

    def _handle_drop(
        self, sources: list[Gio.File], dest_dir: Gio.File, is_copy: bool
    ) -> None:
        def _done(ok: bool, msg: str) -> None:
            self.emit("notify-message", msg if ok else f"Error: {msg}")
            self.refresh()

        if is_copy:
            file_ops.copy_files(sources, dest_dir, on_complete=_done)
        else:
            file_ops.move_files(sources, dest_dir, on_complete=_done)

    def _show_context_menu(
        self, anchor: Gtk.Widget, x: float, y: float, on_selection: bool
    ) -> None:
        if self._active_popover is not None:
            self._active_popover.unparent()
            self._active_popover = None

        menu = Gio.Menu()
        selected = self.get_selected_items()

        if on_selection and selected:
            open_sec = Gio.Menu()
            open_sec.append("Open", "win.open-selected")
            if len(selected) == 1 and selected[0].is_dir:
                open_sec.append("Open in New Tab", "win.open-in-new-tab")
            menu.append_section(None, open_sec)

            edit_sec = Gio.Menu()
            if self.is_trash:
                edit_sec.append("Restore from Trash", "win.restore-trash")
                edit_sec.append("Delete Permanently", "win.delete-permanent")
            else:
                edit_sec.append("Cut", "win.cut")
                edit_sec.append("Copy", "win.copy")
                if len(selected) == 1:
                    edit_sec.append("Rename…", "win.rename")
                edit_sec.append("Move to Trash", "win.trash")
                edit_sec.append("Delete Permanently…", "win.delete-permanent")
            menu.append_section(None, edit_sec)

            extra_sec = Gio.Menu()
            if len(selected) == 1 and selected[0].is_dir:
                extra_sec.append("Add to Bookmarks", "win.bookmark-selected")
            extra_sec.append("Properties", "win.properties")
            menu.append_section(None, extra_sec)
        else:
            if not self.is_trash:
                create_sec = Gio.Menu()
                create_sec.append("New Folder…", "win.new-folder")
                create_sec.append("New File…", "win.new-file")
                create_sec.append("Paste", "win.paste")
                menu.append_section(None, create_sec)

            tools_sec = Gio.Menu()
            tools_sec.append("Open Terminal Here", "win.open-terminal")
            tools_sec.append("Refresh", "win.refresh")
            tools_sec.append("Bookmark This Folder", "win.bookmark-current")
            menu.append_section(None, tools_sec)

        popover = Gtk.PopoverMenu.new_from_model(menu)
        popover.set_parent(anchor)
        popover.set_has_arrow(False)
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)

        def _on_closed(pop: Gtk.PopoverMenu) -> None:
            GLib.idle_add(pop.unparent)
            if self._active_popover is pop:
                self._active_popover = None

        popover.connect("closed", _on_closed)
        self._active_popover = popover
        popover.popup()

    def open_terminal_here(self) -> None:
        path_str = self._current_dir.get_path()
        if not path_str:
            self.emit("notify-message", "Cannot open terminal in non-local directory")
            return
        candidates = [
            "orbit-term",
            "xdg-terminal-exec",
            "ghostty",
            "alacritty",
            "kitty",
            "foot",
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "xterm",
        ]
        for term in candidates:
            if shutil.which(term):
                try:
                    subprocess.Popen([term], cwd=path_str)
                    return
                except OSError:
                    continue
        self.emit("notify-message", "No supported terminal emulator found")
