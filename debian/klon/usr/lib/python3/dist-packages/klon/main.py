import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from .gui.window import MainWindow
from .gui.about import show_about_dialog

class KlonApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.taliskerman.klon',
                         flags=0)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()
        
    def do_startup(self):
        super().do_startup()
        
        # Add About Action
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about_action)
        self.add_action(action)

    def on_about_action(self, action, param):
        win = self.props.active_window
        if win:
            show_about_dialog(win)

def main():
    app = KlonApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
