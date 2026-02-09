import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import restore_from_image

@Gtk.Template(resource_path='/com/taliskerman/klon/restore_page.ui')
class RestorePage(Gtk.Box):
    __gtype_name__ = 'RestorePage'

    restore_source_button = Gtk.Template.Child()
    restore_source_path_label = Gtk.Template.Child()
    restore_dest_dropdown = Gtk.Template.Child()
    restore_btn = Gtk.Template.Child()
    restore_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.selected_file_path = None

        self.restore_source_button.connect("clicked", self.on_file_chooser_clicked)
        self.restore_btn.connect("clicked", self.on_restore_clicked)

        self.refresh_drives()

    def refresh_drives(self):
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.dest_model = Gtk.StringList.new(drive_strings)
        self.restore_dest_dropdown.set_model(self.dest_model)

    def on_file_chooser_clicked(self, btn):
        dialog = Gtk.FileChooserNative(
            title="Select Backup Image",
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.set_modal(True)
        
        dialog.connect("response", self.on_file_response)
        dialog.show()

    def on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_file_path = file.get_path()
            self.restore_source_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_restore_clicked(self, btn):
        dest_idx = self.restore_dest_dropdown.get_selected()
        if dest_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select a destination drive.")
            return
            
        if not self.selected_file_path:
            self.show_error("Please select a source image.")
            return

        dest_drive = self.drives[dest_idx]
        
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
        if response == "restore":
            self.start_restore(dest_path)

    def start_restore(self, dest_path):
        self.restore_btn.set_sensitive(False)
        self.restore_status_label.set_text("Restoring...")
        
        thread = threading.Thread(target=self._run_restore, args=(self.selected_file_path, dest_path))
        thread.daemon = True
        thread.start()

    def _run_restore(self, source, dest):
        try:
            restore_from_image(source, dest, update_callback=self._update_progress)
            GLib.idle_add(self._finished, True, None)
        except Exception as e:
            GLib.idle_add(self._finished, False, str(e))

    def _update_progress(self, line):
        GLib.idle_add(self.restore_status_label.set_text, line)

    def _finished(self, success, error_msg):
        self.restore_btn.set_sensitive(True)
        if success:
            self.restore_status_label.set_text("Restore Complete!")
            self.show_success("Drive restored successfully.")
        else:
            self.restore_status_label.set_text("Restore Failed")
            self.show_error(str(error_msg))

    def show_error(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Error", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Success", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()
