import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import backup_to_image

@Gtk.Template(resource_path='/com/taliskerman/klon/backup_page.ui')
class BackupPage(Gtk.Box):
    __gtype_name__ = 'BackupPage'

    backup_source_dropdown = Gtk.Template.Child()
    backup_dest_button = Gtk.Template.Child()
    backup_dest_path_label = Gtk.Template.Child()
    backup_btn = Gtk.Template.Child()
    backup_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.selected_file_path = None

        self.backup_dest_button.connect("clicked", self.on_file_chooser_clicked)
        self.backup_btn.connect("clicked", self.on_backup_clicked)

        self.refresh_drives()

    def refresh_drives(self):
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.source_model = Gtk.StringList.new(drive_strings)
        self.backup_source_dropdown.set_model(self.source_model)

    def on_file_chooser_clicked(self, btn):
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
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_file_path = file.get_path()
            self.backup_dest_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_backup_clicked(self, btn):
        source_idx = self.backup_source_dropdown.get_selected()
        if source_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select a source drive.")
            return
            
        if not self.selected_file_path:
            self.show_error("Please select a destination file.")
            return

        source_drive = self.drives[source_idx]
        
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
        if response == "backup":
            self.start_backup(source_path)

    def start_backup(self, source_path):
        self.backup_btn.set_sensitive(False)
        self.backup_status_label.set_text("Backing up...")
        
        # In real world, we need root. The backend wrapper uses pkexec.
        thread = threading.Thread(target=self._run_backup, args=(source_path, self.selected_file_path))
        thread.daemon = True
        thread.start()

    def _run_backup(self, source, dest):
        try:
            backup_to_image(source, dest, update_callback=self._update_progress)
            GLib.idle_add(self._finished, True, None)
        except Exception as e:
            GLib.idle_add(self._finished, False, str(e))

    def _update_progress(self, line):
        GLib.idle_add(self.backup_status_label.set_text, line)

    def _finished(self, success, error_msg):
        self.backup_btn.set_sensitive(True)
        if success:
            self.backup_status_label.set_text("Backup Complete!")
            self.show_success(f"Backup saved to {self.selected_file_path}")
        else:
            self.backup_status_label.set_text("Backup Failed")
            self.show_error(str(error_msg))

    def show_error(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Error", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Success", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()
