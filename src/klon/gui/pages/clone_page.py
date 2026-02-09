import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import clone_drive

@Gtk.Template(resource_path='/com/taliskerman/klon/clone_page.ui')
class ClonePage(Gtk.Box):
    __gtype_name__ = 'ClonePage'

    clone_source_dropdown = Gtk.Template.Child()
    clone_dest_dropdown = Gtk.Template.Child()
    clone_button = Gtk.Template.Child()
    clone_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.clone_button.connect("clicked", self.on_clone_clicked)

        # Populate drives
        self.refresh_drives()

    def refresh_drives(self):
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        
        self.source_model = Gtk.StringList.new(drive_strings)
        self.dest_model = Gtk.StringList.new(drive_strings)
        
        self.clone_source_dropdown.set_model(self.source_model)
        self.clone_dest_dropdown.set_model(self.dest_model)

    def on_clone_clicked(self, button):
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

        # Confirm Dialog
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
        if response == "clone":
            self.start_cloning(source_drive, dest_drive)

    def start_cloning(self, source, dest):
        self.clone_button.set_sensitive(False)
        self.clone_status_label.set_text("Cloning in progress...")
        
        thread = threading.Thread(target=self._run_clone, args=(source.path, dest.path))
        thread.daemon = True
        thread.start()

    def _run_clone(self, source_path, dest_path):
        try:
            clone_drive(source_path, dest_path, update_callback=self._update_progress)
            GLib.idle_add(self._clone_finished, True, None)
        except Exception as e:
            GLib.idle_add(self._clone_finished, False, str(e))

    def _update_progress(self, status_line):
        GLib.idle_add(self.clone_status_label.set_text, status_line)

    def _clone_finished(self, success, error_msg):
        self.clone_button.set_sensitive(True)
        if success:
            self.clone_status_label.set_text("Cloning Complete!")
            self.show_success("Drive cloned successfully.")
        else:
            self.clone_status_label.set_text("Cloning Failed")
            self.show_error(f"Error: {error_msg}")

    def show_error(self, message):
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Error",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, message):
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Success",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.present()
