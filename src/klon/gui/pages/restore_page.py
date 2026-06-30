"""Restore page UI controller.

This module maps controls on the "Restore" tab, letting users choose a backup raw
disk image, designate a destination block device, and flash it back in the background.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import restore_from_image

@Gtk.Template(resource_path='/com/taliskerman/klon/restore_page.ui')
class RestorePage(Gtk.Box):
    """Layout controller class for disk restore UI.

    Loads backup files using Gtk.FileChooserNative dialogs, dropdown queries
    for physical destination drives, and runs restore operations asynchronously.
    """
    __gtype_name__ = 'RestorePage'

    # Template child UI elements defined in restore_page.ui
    restore_source_button = Gtk.Template.Child()
    restore_source_path_label = Gtk.Template.Child()
    restore_dest_dropdown = Gtk.Template.Child()
    restore_btn = Gtk.Template.Child()
    restore_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        """Initialize RestorePage widget elements.

        Args:
            window: Parent Gtk.Window hosting this page.
        """
        super().__init__(**kwargs)
        self.window = window
        self.selected_file_path = None

        self.restore_source_button.connect("clicked", self.on_file_chooser_clicked)
        self.restore_btn.connect("clicked", self.on_restore_clicked)

        self.refresh_drives()

    def refresh_drives(self):
        """Scan physical drives via backend list_drives and populate the destination dropdown."""
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.dest_model = Gtk.StringList.new(drive_strings)
        self.restore_dest_dropdown.set_model(self.dest_model)

    def on_file_chooser_clicked(self, _button):
        """Open a native file chooser dialog in OPEN mode to import a raw backup image.

        Args:
            _button: The Gtk.Button trigger widget.
        """
        dialog = Gtk.FileChooserNative(
            title="Select Backup Image",
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.set_modal(True)
        
        dialog.connect("response", self.on_file_response)
        dialog.show()

    def on_file_response(self, dialog, response):
        """Handle Gtk.FileChooserNative response callbacks.

        Args:
            dialog: The FileChooserNative dialog.
            response: Response identifier Gtk.ResponseType.
        """
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_file_path = file.get_path()
            self.restore_source_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_restore_clicked(self, _button):
        """Validate options and request confirmation warning dialog before writing.

        Args:
            _button: The Gtk.Button trigger widget.
        """
        dest_idx = self.restore_dest_dropdown.get_selected()
        if dest_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select a destination drive.")
            return
            
        if not self.selected_file_path:
            self.show_error("Please select a source image.")
            return

        dest_drive = self.drives[dest_idx]
        
        # Confirmation dialog is required as restoring completely overwrites target blocks
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Confirm Restore",
            body=f"Restore {self.selected_file_path} to {dest_drive.name}?\n\nALL DATA ON {dest_drive.name} WILL BE LOST!",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("restore", "Start Restore")
        dialog.set_response_appearance("restore", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_confirm_response, dest_drive.path)
        dialog.present()

    def on_confirm_response(self, dialog, response, dest_path):
        """Evaluate confirmation responses to trigger image restore.

        Args:
            dialog: The MessageDialog instance.
            response: Response identifier string.
            dest_path: Destination device path node.
        """
        if response == "restore":
            self.start_restore(dest_path)

    def start_restore(self, dest_path: str):
        """Disable button, set status labels, and spawn the restore daemon thread.

        Args:
            dest_path: Destination block device node.
        """
        self.restore_btn.set_sensitive(False)
        self.restore_status_label.set_text("Restoring...")
        
        thread = threading.Thread(target=self._run_restore, args=(self.selected_file_path, dest_path))
        thread.daemon = True
        thread.start()

    def _run_restore(self, source: str, dest: str):
        """Worker thread entrypoint executing backend restore image calls.

        Args:
            source: Source backup image path.
            dest: Target USB drive path.
        """
        try:
            restore_from_image(source, dest, update_callback=self._update_progress)
            GLib.idle_add(self._finished, True, None)
        except Exception as error:
            GLib.idle_add(self._finished, False, str(error))

    def _update_progress(self, line: str):
        """Callback to marshal restore status messages back to the UI.

        Args:
            line: Status details reported by dd.
        """
        GLib.idle_add(self.restore_status_label.set_text, line)

    def _finished(self, success: bool, error_msg: str):
        """Update buttons status, set final status labels, and show alert dialogs.

        Args:
            success: Whether the restore completed successfully.
            error_msg: String explaining errors if success is False.
        """
        self.restore_btn.set_sensitive(True)
        if success:
            self.restore_status_label.set_text("Restore Complete!")
            self.show_success("Drive restored successfully.")
        else:
            self.restore_status_label.set_text("Restore Failed")
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

