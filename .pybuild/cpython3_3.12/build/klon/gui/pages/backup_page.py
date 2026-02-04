import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import backup_to_image

class BackupPage(Adw.PreferencesPage):
    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        
        self.set_title("Backup to Image")
        self.set_icon_name("document-save-symbolic")

        # Configuration Group
        self.conf_group = Adw.PreferencesGroup()
        self.conf_group.set_title("Backup Configuration")
        self.conf_group.set_description("Create a disk image of a drive.")
        self.add(self.conf_group)

        # Source Drive Row
        self.source_row = Adw.ActionRow()
        self.source_row.set_title("Source Drive")
        self.source_row.set_subtitle("The drive to back up")
        self.conf_group.add(self.source_row)

        self.source_dropdown = Gtk.DropDown()
        self.source_dropdown.set_valign(Gtk.Align.CENTER)
        self.source_row.add_suffix(self.source_dropdown)

        # Destination File Row
        self.dest_row = Adw.ActionRow()
        self.dest_row.set_title("Destination Image")
        self.dest_row.set_subtitle("Where to save the .img file")
        self.conf_group.add(self.dest_row)

        self.file_chooser_btn = Gtk.Button(icon_name="folder-open-symbolic")
        self.file_chooser_btn.set_valign(Gtk.Align.CENTER)
        self.file_chooser_btn.connect("clicked", self.on_file_chooser_clicked)
        self.dest_row.add_suffix(self.file_chooser_btn)
        
        self.dest_path_label = Gtk.Label(label="No file selected")
        self.dest_path_label.add_css_class("dim-label")
        self.dest_path_label.set_valign(Gtk.Align.CENTER)
        self.dest_path_label.set_margin_end(10)
        self.dest_row.add_suffix(self.dest_path_label)

        self.selected_file_path = None

        # Action Group
        self.action_group = Adw.PreferencesGroup()
        self.add(self.action_group)

        # Backup Button
        self.backup_btn = Gtk.Button(label="Start Backup")
        self.backup_btn.add_css_class("suggested-action")
        self.backup_btn.add_css_class("pill")
        self.backup_btn.connect("clicked", self.on_backup_clicked)
        self.backup_btn.set_margin_top(20)
        self.backup_btn.set_halign(Gtk.Align.CENTER)
        self.action_group.add(self.backup_btn)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_margin_top(10)
        self.action_group.add(self.status_label)

        self.refresh_drives()

    def refresh_drives(self):
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.source_model = Gtk.StringList.new(drive_strings)
        self.source_dropdown.set_model(self.source_model)

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
            self.dest_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_backup_clicked(self, btn):
        source_idx = self.source_dropdown.get_selected()
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
        self.status_label.set_text("Backing up...")
        
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
        GLib.idle_add(self.status_label.set_text, line)

    def _finished(self, success, error_msg):
        self.backup_btn.set_sensitive(True)
        if success:
            self.status_label.set_text("Backup Complete!")
            self.show_success(f"Backup saved to {self.selected_file_path}")
        else:
            self.status_label.set_text("Backup Failed")
            self.show_error(str(error_msg))

    def show_error(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Error", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Success", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()
