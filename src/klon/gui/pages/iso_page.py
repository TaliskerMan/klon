"""Recovery USB creation and Live ISO downloader tab UI controller.

This module maps controls on the "Recovery USB" tab, letting users download the
standard live Debian Linux ISO image or import their own ISO, and flash it to a USB drive.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading
import os

from ...backend.drives import list_drives
from ...backend.iso import download_iso, flash_iso_and_setup_persistence, DEFAULT_ISO_URL, DEFAULT_ISO_NAME

@Gtk.Template(resource_path='/com/taliskerman/klon/iso_page.ui')
class IsoPage(Gtk.Box):
    """Layout controller class for Recovery USB flashing UI.

    Handles remote ISO downloads via stream requests, parses local ISO files from
    Gtk.FileChooserNative dialogs, and flashes block devices using backend helpers.
    """
    __gtype_name__ = 'IsoPage'

    # Template child UI elements defined in iso_page.ui
    iso_dl_button = Gtk.Template.Child()
    iso_file_btn = Gtk.Template.Child()
    iso_path_label = Gtk.Template.Child()
    iso_target_dropdown = Gtk.Template.Child()
    iso_create_btn = Gtk.Template.Child()
    iso_status_label = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        """Initialize IsoPage classes and pre-check default download destinations.

        Args:
            window: Parent Gtk.Window hosting this page.
        """
        super().__init__(**kwargs)
        self.window = window
        self.selected_iso_path = None

        self.iso_dl_button.connect("clicked", self.on_download_clicked)
        self.iso_file_btn.connect("clicked", self.on_file_chooser_clicked)
        self.iso_create_btn.connect("clicked", self.on_create_clicked)

        # Check standard location for downloaded ISOs
        default_dl = os.path.expanduser(f"~/Downloads/{DEFAULT_ISO_NAME}")
        if os.path.exists(default_dl):
            self.selected_iso_path = default_dl
            self.iso_path_label.set_text(DEFAULT_ISO_NAME)

        self.refresh_drives()

    def refresh_drives(self):
        """Refresh system physical drives and populate the target USB dropdown."""
        self.drives = list_drives()
        drive_strings = [f"{d.model} ({d.name}) - {d.size}" for d in self.drives]
        self.dest_model = Gtk.StringList.new(drive_strings)
        self.iso_target_dropdown.set_model(self.dest_model)

    def on_download_clicked(self, btn):
        """Trigger background ISO download stream.

        Args:
            btn: The Gtk.Button trigger widget.
        """
        self.iso_dl_button.set_sensitive(False)
        self.iso_status_label.set_text("Downloading ISO...")
        target_path = os.path.expanduser(f"~/Downloads/{DEFAULT_ISO_NAME}")
        
        thread = threading.Thread(target=self._run_download, args=(DEFAULT_ISO_URL, target_path))
        thread.daemon = True
        thread.start()

    def _run_download(self, url: str, path: str):
        """Worker thread entrypoint executing requests GET stream downloads.

        Args:
            url: Remote ISO URL.
            path: Target local file location.
        """
        success = download_iso(url, path, progress_callback=self._update_dl_progress)
        GLib.idle_add(self._dl_finished, success, path)

    def _update_dl_progress(self, percent: float, msg: str):
        """Callback to marshal download status updates back to the UI.

        Args:
            percent: Download percentage (unused in text updates).
            msg: Custom message indicating progress.
        """
        GLib.idle_add(self.iso_status_label.set_text, msg)

    def _dl_finished(self, success: bool, path: str):
        """Update download buttons status and set target ISO paths on success.

        Args:
            success: Whether the download succeeded.
            path: Path where the ISO was downloaded.
        """
        self.iso_dl_button.set_sensitive(True)
        if success:
            self.iso_status_label.set_text("Download Complete!")
            self.selected_iso_path = path
            self.iso_path_label.set_text(os.path.basename(path))
        else:
            self.iso_status_label.set_text("Download Failed")

    def on_file_chooser_clicked(self, btn):
        """Open a native file chooser dialog in OPEN mode to import a custom ISO.

        Args:
            btn: The Gtk.Button trigger widget.
        """
        dialog = Gtk.FileChooserNative(
            title="Select ISO",
            transient_for=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.set_modal(True)
        
        dialog.connect("response", self.on_file_response)
        dialog.show()

    def on_file_response(self, dialog, response):
        """Handle custom file response selections.

        Args:
            dialog: The FileChooserNative dialog.
            response: Response identifier Gtk.ResponseType.
        """
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            self.selected_iso_path = file.get_path()
            self.iso_path_label.set_text(file.get_basename())
        dialog.destroy()

    def on_create_clicked(self, btn):
        """Validate options and request confirmation to begin flashing.

        Args:
            btn: The Gtk.Button trigger widget.
        """
        dest_idx = self.iso_target_dropdown.get_selected()
        if dest_idx == Gtk.INVALID_LIST_POSITION:
            self.show_error("Please select a target USB drive.")
            return
            
        if not self.selected_iso_path:
            self.show_error("Please select an ISO image.")
            return

        dest_drive = self.drives[dest_idx]
        
        # Flashing completely erases target devices, warranting a warning dialog
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Confirm Flash",
            body=f"Flash {os.path.basename(self.selected_iso_path)} to {dest_drive.name}?\n\nThis will ERASE ALL DATA on {dest_drive.name}!",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("flash", "Flash Drive")
        dialog.set_response_appearance("flash", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_confirm_response, dest_drive.path)
        dialog.present()

    def on_confirm_response(self, dialog, response, dest_path):
        """Evaluate confirmation responses to trigger USB flashing.

        Args:
            dialog: The MessageDialog instance.
            response: Response identifier string.
            dest_path: Destination device path node.
        """
        if response == "flash":
            self.start_flash(dest_path)

    def start_flash(self, dest_path: str):
        """Disable button, set status messages, and start the daemon flash thread.

        Args:
            dest_path: Destination USB block device node.
        """
        self.iso_create_btn.set_sensitive(False)
        self.iso_status_label.set_text("Flashing...")
        
        thread = threading.Thread(target=self._run_flash, args=(self.selected_iso_path, dest_path))
        thread.daemon = True
        thread.start()

    def _run_flash(self, iso: str, dest: str):
        """Worker thread entrypoint executing backend flash routines.

        Args:
            iso: Source ISO path.
            dest: Target USB drive path.
        """
        try:
            flash_iso_and_setup_persistence(iso, dest, progress_callback=self._update_progress)
            GLib.idle_add(self._finished, True, None)
        except Exception as e:
            GLib.idle_add(self._finished, False, str(e))

    def _update_progress(self, percent: float, msg: str):
        """Callback to marshal flashing progress messages back to the UI.

        Args:
            percent: Flash progress percentage (unused in text updates).
            msg: Message details reported by dd.
        """
        GLib.idle_add(self.iso_status_label.set_text, msg)

    def _finished(self, success: bool, error_msg: str):
        """Update buttons status, set final status labels, and show alert dialogs.

        Args:
            success: Whether the flashing process finished successfully.
            error_msg: String explaining errors if success is False.
        """
        self.iso_create_btn.set_sensitive(True)
        if success:
            self.iso_status_label.set_text("Recovery Drive Created!")
            self.show_success("ISO Flashed Successfully.\n\nNote: Persistence partition creation is experimental/manual in this version.")
        else:
            self.iso_status_label.set_text("Flash Failed")
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

