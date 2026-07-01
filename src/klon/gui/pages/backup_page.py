"""Backup page UI controller.

This module maps UI handlers to the backup tab in the MainWindow, permitting users
to select a block device and backup target path to dump raw disk images in the background.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import backup_to_image
from ...backend.safety import UnsafeOperationError


def _drive_label(d):
    """Human label including any mountpoint(s) so in-use disks are obvious."""
    mounts = []
    if getattr(d, "mountpoint", None):
        mounts.append(d.mountpoint)
    for child in getattr(d, "children", []) or []:
        if getattr(child, "mountpoint", None):
            mounts.append(child.mountpoint)
    suffix = f" — mounted: {', '.join(mounts)}" if mounts else ""
    return f"{d.model} ({d.name}) - {d.size}{suffix}"

@Gtk.Template(resource_path='/com/taliskerman/klon/backup_page.ui')
class BackupPage(Gtk.Box):
    """Layout controller class for disk backup UI.

    Binds widgets from backup_page.ui to local attributes, triggers file selection
    native dialogs, and delegates the raw image creation task to a background thread.
    """
    __gtype_name__ = 'BackupPage'

    # Template child UI elements defined in backup_page.ui
    backup_source_dropdown = Gtk.Template.Child()
    backup_dest_button = Gtk.Template.Child()
    backup_dest_path_label = Gtk.Template.Child()
    backup_btn = Gtk.Template.Child()
    backup_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        """Initialize BackupPage widget instances and connect event signals.

        Args:
            window: Parent Gtk.Window hosting this page, used as transient anchor.
        """
        super().__init__(**kwargs)
        self.window = window
        self.selected_file_path = None

        self.backup_dest_button.connect("clicked", self.on_file_chooser_clicked)
        self.backup_btn.connect("clicked", self.on_backup_clicked)

        self.refresh_drives()

    def refresh_drives(self):
        """Scan physical drives via backend list_drives and populate the dropdown menu."""
        self.drives = list_drives()
        drive_strings = [_drive_label(d) for d in self.drives]
        self.source_model = Gtk.StringList.new(drive_strings)
        self.backup_source_dropdown.set_model(self.source_model)

    def on_file_chooser_clicked(self, _button):
        """Open a native file chooser dialog in SAVE mode to designate the backup image path.

        Args:
            _button: The Gtk.Button trigger widget.
        """
        dialog = Gtk.FileChooserNative(
            title="Save Backup Image",
            transient_for=self.window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.set_modal(True)
        dialog.set_current_name("backup.img")
        
        dialog.connect("response", self.on_file_response)
        dialog.show()

    def on_file_response(self, dialog, response):
        """Handle Gtk.FileChooserNative response callbacks.

        Args:
            dialog: The FileChooserNative dialog instance.
            response: Gtk.ResponseType indicating user choices (e.g. ACCEPT, CANCEL).
        """
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_file_path = file.get_path()
            self.backup_dest_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_backup_clicked(self, _button):
        """Validate input parameters and trigger the confirmation dialog.

        Args:
            _button: The Gtk.Button trigger widget.
        """
        source_idx = self.backup_source_dropdown.get_selected()
        if source_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select a source drive.")
            return
            
        if not self.selected_file_path:
            self.show_error("Please select a destination file.")
            return

        source_drive = self.drives[source_idx]
        
        # Confirmation dialog is required as backing up can be long-running
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Confirm Backup",
            body=f"Back up {source_drive.name} to {self.selected_file_path}?\nThis may take a while.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("backup", "Start Backup")
        dialog.set_response_appearance("backup", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self.on_confirm_response, source_drive.path)
        dialog.present()

    def on_confirm_response(self, dialog, response, source_path):
        """Evaluate confirmation responses to trigger the backup task.

        Args:
            dialog: The MessageDialog instance.
            response: Response identifier string.
            source_path: Target drive source path node.
        """
        if response == "backup":
            self.start_backup(source_path)

    def start_backup(self, source_path: str):
        """Disable buttons, status message updating, and spawn a daemon worker thread.

        Args:
            source_path: The physical drive path.
        """
        self.backup_btn.set_sensitive(False)
        self.backup_status_label.set_text("Backing up...")
        
        # Thread delegation prevents UI locking. The subprocess will prompt for sudo permissions using pkexec.
        thread = threading.Thread(target=self._run_backup, args=(source_path, self.selected_file_path))
        thread.daemon = True
        thread.start()

    def _run_backup(self, source: str, dest: str):
        """Worker thread entrypoint executing backend backup image calls.

        Args:
            source: Source device path.
            dest: Target backup image path.
        """
        try:
            backup_to_image(source, dest, update_callback=self._update_progress)
            GLib.idle_add(self._finished, "ok", None)
        except UnsafeOperationError as error:
            GLib.idle_add(self._finished, "refused", str(error))
        except Exception as error:
            GLib.idle_add(self._finished, "failed", str(error))

    def _update_progress(self, line: str):
        """Callback to marshal status messages back to the GTK main UI loop.

        Args:
            line: Status details reported by dd.
        """
        GLib.idle_add(self.backup_status_label.set_text, line)

    def _finished(self, status: str, error_msg: str):
        """Update buttons status, set final status labels, and show alert dialogs.

        Args:
            status: One of "ok", "refused", or "failed".
            error_msg: String explaining errors for the non-"ok" outcomes.
        """
        self.backup_btn.set_sensitive(True)
        if status == "ok":
            self.backup_status_label.set_text("Backup Complete!")
            self.show_success(f"Backup saved to {self.selected_file_path}")
        elif status == "refused":
            self.backup_status_label.set_text("Refused for safety")
            self.show_error(str(error_msg))
        else:
            self.backup_status_label.set_text("Backup Failed")
            self.show_error(str(error_msg))

    def show_error(self, msg: str):
        """Display an Adw.MessageDialog warning popup.

        Args:
            msg: The error description.
        """
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Error", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, msg: str):
        """Display an Adw.MessageDialog confirmation popup.

        Args:
            msg: The success message.
        """
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Success", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

