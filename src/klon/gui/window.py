"""Application main window definition.

This module loads the main window XML layout definition from GResource via Gtk.Template,
instantiates its sub-page layouts, and appends them to the Adw.ViewStack.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .pages.clone_page import ClonePage
from .pages.backup_page import BackupPage
from .pages.restore_page import RestorePage
from .pages.iso_page import IsoPage

@Gtk.Template(resource_path='/com/taliskerman/klon/mainwindow.ui')
class MainWindow(Adw.ApplicationWindow):
    """The central application window class for Klon.

    Loads the mainwindow.ui template, binding template child widgets, and
    attaches the subpage view stack.
    """
    __gtype_name__ = 'MainWindow'

    # Template child UI elements defined in mainwindow.ui
    view_stack = Gtk.Template.Child()
    main_menu = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        """Initialize the MainWindow and programmatically append page widgets to the view stack."""
        super().__init__(*args, **kwargs)

        # Instantiate each functional page view, passing self as the transient parent window
        self.clone_page = ClonePage(window=self)
        self.view_stack.add_titled(self.clone_page, "clone", "Clone")
        
        self.backup_page = BackupPage(window=self)
        self.view_stack.add_titled(self.backup_page, "backup", "Backup")
        
        self.restore_page = RestorePage(window=self)
        self.view_stack.add_titled(self.restore_page, "restore", "Restore")

        self.iso_page = IsoPage(window=self)
        self.view_stack.add_titled(self.iso_page, "recovery", "Recovery USB")


