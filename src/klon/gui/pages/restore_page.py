import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading

from ...backend.drives import list_drives
from ...backend.clone import restore_from_image

class RestorePage(Adw.PreferencesPage):
    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        
        self.set_title("Restore from Image")
        self.set_icon_name("klon-restore")

        # Configuration Group
        self.conf_group = Adw.PreferencesGroup()
        self.conf_group.set_title("Restore Configuration")
        self.conf_group.set_description("Restore a disk image to a drive. WARN: Overwrites the drive.")
        self.add(self.conf_group)

        # Source File Row
        self.source_row = Adw.ActionRow()
        self.source_row.set_title("Source Image")
        self.source_row.set_subtitle("The .img file to restore")
        self.conf_group.add(self.source_row)

        self.file_chooser_btn = Gtk.Button(icon_name="folder-open-symbolic")
        self.file_chooser_btn.set_valign(Gtk.Align.CENTER)
        self.file_chooser_btn.connect("clicked", self.on_file_chooser_clicked)
        self.source_row.add_suffix(self.file_chooser_btn)
        
        self.source_path_label = Gtk.Label(label="No file selected")
        self.source_path_label.add_css_class("dim-label")
        self.source_path_label.set_valign(Gtk.Align.CENTER)
        self.source_path_label.set_margin_end(10)
        self.source_row.add_suffix(self.source_path_label)

        self.selected_file_path = None

        # Destination Drive Row
        self.dest_row = Adw.ActionRow()
        self.dest_row.set_title("Destination Drive")
        self.dest_row.set_subtitle("The drive to be overwritten")
        self.conf_group.add(self.dest_row)

        self.dest_dropdown = Gtk.DropDown()
        self.dest_dropdown.set_valign(Gtk.Align.CENTER)
        self.dest_row.add_suffix(self.dest_dropdown)

        # Action Group
        self.action_group = Adw.PreferencesGroup()
        self.add(self.action_group)

        # Restore Button
        self.restore_btn = Gtk.Button(label="Start Restore")
        self.restore_btn.add_css_class("destructive-action") # Red button for dangerous action
        self.restore_btn.add_css_class("pill")
        self.restore_btn.connect("clicked", self.on_restore_clicked)
        self.restore_btn.set_margin_top(20)
        self.restore_btn.set_halign(Gtk.Align.CENTER)
        self.action_group.add(self.restore_btn)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_margin_top(10)
        self.action_group.add(self.status_label)

        self.refresh_drives()

    def refresh_drives(self):
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.dest_model = Gtk.StringList.new(drive_strings)
        self.dest_dropdown.set_model(self.dest_model)

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
            self.source_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_restore_clicked(self, btn):
        dest_idx = self.dest_dropdown.get_selected()
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
        self.status_label.set_text("Restoring...")
        
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
        GLib.idle_add(self.status_label.set_text, line)

    def _finished(self, success, error_msg):
        self.restore_btn.set_sensitive(True)
        if success:
            self.status_label.set_text("Restore Complete!")
            self.show_success("Drive restored successfully.")
        else:
            self.status_label.set_text("Restore Failed")
            self.show_error(str(error_msg))

    def show_error(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Error", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_success(self, msg):
        dialog = Adw.MessageDialog(transient_for=self.window, heading="Success", body=msg)
        dialog.add_response("ok", "OK")
        dialog.present()
