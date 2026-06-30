"""Direct disk-to-disk cloning tab UI controller.

This module controls the UI logic on the "Clone" tab, permitting users to choose
a source and target physical disk, validating the inputs, requiring verification
since cloning is destructive, and running the `dd` cloning process in the background.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import clone_drive

@Gtk.Template(resource_path='/com/taliskerman/klon/clone_page.ui')
class ClonePage(Gtk.Box):
    """Layout controller class for disk-to-disk cloning UI.

    Binds widgets from clone_page.ui, handles dropdown inputs, double-confirms
    destructive writing, and delegates cloning operation to a daemon worker thread.
    """
    __gtype_name__ = 'ClonePage'

    # Template child UI elements defined in clone_page.ui
    clone_source_dropdown = Gtk.Template.Child()
    clone_dest_dropdown = Gtk.Template.Child()
    clone_button = Gtk.Template.Child()
    clone_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        """Initialize ClonePage class instances.

        Args:
            window: Parent Gtk.Window hosting this page.
        """
        super().__init__(**kwargs)
        self.window = window
        self.clone_button.connect("clicked", self.on_clone_clicked)

        # Populate physical drive selections
        self.refresh_drives()

    def refresh_drives(self):
        """Refresh system physical drives and populate source and destination dropdowns."""
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        
        self.source_model = Gtk.StringList.new(drive_strings)
        self.dest_model = Gtk.StringList.new(drive_strings)
        
        self.clone_source_dropdown.set_model(self.source_model)
        self.clone_dest_dropdown.set_model(self.dest_model)

    def on_clone_clicked(self, button):
        """Validate dropdown selections and raise confirmation dialog.

        Args:
            button: The Gtk.Button trigger widget.
        """
        source_idx = self.clone_source_dropdown.get_selected()
        dest_idx = self.clone_dest_dropdown.get_selected()
        
        if source_idx == Gtk.INVALID_LIST_POSITION or dest_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select both drives.")
            return

        source_drive = self.drives[source_idx]
        dest_drive = self.drives[dest_idx]

        if source_drive.path == dest_drive.path:
            self.show_error("Source and Destination cannot be the same drive.")
            return

        # Explicit destructive warning dialog
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Confirm Cloning",
            body=f"Are you sure you want to clone {source_drive.name} to {dest_drive.name}?\n\nALL DATA ON {dest_drive.name} WILL BE LOST!",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("clone", "Clone Drive")
        dialog.set_response_appearance("clone", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_confirm_response, source_drive, dest_drive)
        dialog.present()

    def on_confirm_response(self, dialog, response, source_drive, dest_drive):
        """Evaluate confirmation responses to trigger cloning.

        Args:
            dialog: The MessageDialog instance.
            response: Response identifier string.
            source_drive: Source Drive dataclass instance.
            dest_drive: Destination Drive dataclass instance.
        """
        if response == "clone":
            self.start_cloning(source_drive, dest_drive)

    def start_cloning(self, source, dest):
        """Disable buttons, set status messages, and start the clone worker thread.

        Args:
            source: Source Drive dataclass instance.
            dest: Target Drive dataclass instance.
        """
        self.clone_button.set_sensitive(False)
        self.clone_status_label.set_text("Cloning in progress...")
        
        # Thread worker spawns pkexec subprocess and captures stderr lines
        thread = threading.Thread(target=self._run_clone, args=(source.path, dest.path))
        thread.daemon = True
        thread.start()

    def _run_clone(self, source_path: str, dest_path: str):
        """Worker thread entrypoint executing backend clone commands.

        Args:
            source_path: Target drive source path node.
            dest_path: Target drive destination path node.
        """
        try:
            clone_drive(source_path, dest_path, update_callback=self._update_progress)
            GLib.idle_add(self._clone_finished, True, None)
        except Exception as error:
            GLib.idle_add(self._clone_finished, False, str(error))

    def _update_progress(self, status_line: str):
        """Callback to marshal status messages back to the GTK main UI loop.

        Args:
            status_line: Status details reported by dd.
        """
        GLib.idle_add(self.clone_status_label.set_text, status_line)

    def _clone_finished(self, success: bool, error_msg: str):
        """Update buttons status, set final status labels, and show alert dialogs.

        Args:
            success: Whether cloning completed successfully.
            error_msg: String explaining errors if success is False.
        """
        self.clone_button.set_sensitive(True)
        if success:
            self.clone_status_label.set_text("Cloning Complete!")
            self.show_success("Drive cloned successfully.")
        else:
            self.clone_status_label.set_text("Cloning Failed")
            self.show_error(f"Error: {error_msg}")

    def show_error(self, message: str):
        """Display an Adw.MessageDialog warning popup.

        Args:
            message: The error description.
        """
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Error",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, message: str):
        """Display an Adw.MessageDialog confirmation popup.

        Args:
            message: The success message.
        """
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Success",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

