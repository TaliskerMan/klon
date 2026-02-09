import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk

# from .gui.window import MainWindow
from .gui.about import show_about_dialog

class KlonApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.taliskerman.klon',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        from .gui.window import MainWindow
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()
        
    def do_startup(self):
        Adw.Application.do_startup(self)

        # Load GResource
        try:
            from importlib.resources import files
            resource_file = files('klon').joinpath('klon.gresource')
            resource = Gio.Resource.load(str(resource_file))
            resource._register()
        except Exception as e:
            print(f"Failed to load GResource: {e}")

        # Load CSS (from resource now)
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_resource('/com/taliskerman/klon/style.css')
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Failed to load CSS: {e}")

        # Add Icon Resource Path
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_resource_path('/com/taliskerman/klon')
        
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
