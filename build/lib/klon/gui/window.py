import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .pages.clone_page import ClonePage
from .pages.backup_page import BackupPage
from .pages.restore_page import RestorePage
from .pages.iso_page import IsoPage

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Klon")
        self.set_default_size(800, 600)

        # Main Box
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.box)

        # Header Bar with View Switcher Title
        self.header = Adw.HeaderBar()
        self.box.append(self.header)

        self.view_switcher_title = Adw.ViewSwitcherTitle()
        self.header.set_title_widget(self.view_switcher_title)

        # Menu Button in Header
        menu = Gio.Menu()
        menu.append("About Klon", "app.about")
        
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(menu)
        self.header.pack_end(menu_button)

        # View Stack
        self.stack = Adw.ViewStack()
        self.box.append(self.stack)
        self.stack.set_vexpand(True)

        # Bind Switcher to Stack
        self.view_switcher_title.set_stack(self.stack)

        # Add Pages
        self.clone_page = ClonePage(window=self)
        self.stack.add_titled(self.clone_page, "clone", "Clone")
        
        self.backup_page = BackupPage(window=self)
        self.stack.add_titled(self.backup_page, "backup", "Backup")
        
        self.restore_page = RestorePage(window=self)
        self.stack.add_titled(self.restore_page, "restore", "Restore")

        self.iso_page = IsoPage(window=self)
        self.stack.add_titled(self.iso_page, "recovery", "Recovery USB")

