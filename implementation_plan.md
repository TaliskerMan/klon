# Implementation Plan - Integrate UI Templates

This plan details the steps to replace the programmatic UI construction in Klon's Python code with the `klon_app.ui` templates.

## User Review Required
> [!IMPORTANT]
> This is a refactor of the application's core UI logic. The application might be unstable until all pages are converted.

## Proposed Changes

### Window & Resources (`window.py`, `app.py`)

#### [MODIFY] [window.py](file:///home/freecode/antigrav/klon/src/klon/gui/window.py)
- Use `@Gtk.Template(resource_path='/com/taliskerman/klon/klon_app.ui')`
- Remove manual `self.box`, `self.header`, `self.stack` creation.
- Map `@Gtk.Template.Child` for `view_stack` and `main_menu`.

#### [MODIFY] [app.py](file:///home/freecode/antigrav/klon/src/klon/app.py) (Wait, `main.py` is entry) -> `main.py`
- Ensure `Gio.Resource` is loaded or the `.ui` file is loaded from disk for development.
- *Dev Note:* Since we don't have a compiled `gresource` yet, I will use `Gtk.Builder` or `set_template_from_file` (if available via trickery) or more standardly, **load the UI file content and set it as the template bytes**.
- *Simpler Approach:* Use `class` + `set_template` in `__class_init__`.

### Pages (`clone_page.py`, etc.)

#### [MODIFY] [clone_page.py](file:///home/freecode/antigrav/klon/src/klon/gui/pages/clone_page.py)
- Decorate class with `@Gtk.Template`.
- Map children: `clone_source_dropdown`, `clone_dest_dropdown`, `clone_button`, `clone_status_label`.
- Remove `__init__` UI build code.
- Keep `refresh_drives` and `on_clone_clicked` logic.

#### [MODIFY] [backup_page.py](file:///home/freecode/antigrav/klon/src/klon/gui/pages/backup_page.py)
- Map: `backup_source_dropdown`, `backup_dest_button`, `backup_dest_path_label`, `backup_btn`, `backup_status_label`.

#### [MODIFY] [restore_page.py](file:///home/freecode/antigrav/klon/src/klon/gui/pages/restore_page.py)
- Map: `restore_source_button`, `restore_source_path_label`, `restore_dest_dropdown`, `restore_btn`, `restore_status_label`.

#### [MODIFY] [iso_page.py](file:///home/freecode/antigrav/klon/src/klon/gui/pages/iso_page.py)
- Map: `iso_dl_button`, `iso_file_btn`, `iso_path_label`, `iso_target_dropdown`, `iso_create_btn`, `iso_status_label`.

## Verification Plan

### Automated Tests
- None available for GUI.

### Manual Verification
- Run the application (`python3 -m klon.main`).
- Verify each page loads and controls are accessible.
- Verify actions (buttons) trigger the expected methods (logic preservation).
