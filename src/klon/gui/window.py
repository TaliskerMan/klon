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
    __gtype_name__ = 'MainWindow'

    view_stack = Gtk.Template.Child()
    main_menu = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Pages (programmatically for now, but inserted into template stack)
        self.clone_page = ClonePage(window=self)
        self.view_stack.add_titled(self.clone_page, "clone", "Clone")
        
        self.backup_page = BackupPage(window=self)
        self.view_stack.add_titled(self.backup_page, "backup", "Backup")
        
        self.restore_page = RestorePage(window=self)
        self.view_stack.add_titled(self.restore_page, "restore", "Restore")

        self.iso_page = IsoPage(window=self)
        self.view_stack.add_titled(self.iso_page, "recovery", "Recovery USB")

