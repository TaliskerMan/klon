"""Main entry point for the Klon GTK4/Libadwaita application.

This module initializes logging, loads the compiled GResource bundle, registers
custom CSS stylesheets and application icons, and starts the Adw.Application loop.
"""

import sys
import os
import logging
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk

# from .gui.window import MainWindow
from .gui.about import show_about_dialog

class KlonApp(Adw.Application):
    """The main Libadwaita Application class for Klon.

    Orchestrates application lifecycle events including startup setup, resource loading,
    and main window activation/presentation.
    """

    def __init__(self):
        """Initialize KlonApp with its unique application ID and default execution flags."""
        super().__init__(application_id='com.taliskerman.klon',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        """Handle application activation by creating or focusing the MainWindow."""
        from .gui.window import MainWindow
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()
        
    def do_startup(self):
        """Execute early initialization tasks such as GResource and CSS loading."""
        Adw.Application.do_startup(self)

        # Load GResource bundle containing XML UI definitions and assets.
        # This allows us to load layout definitions via Gtk.Template declarations.
        try:
            from importlib.resources import files
            resource_file = files('klon').joinpath('klon.gresource')
            resource = Gio.Resource.load(str(resource_file))
            resource._register()
        except Exception as e:
            logging.error(f"Failed to load GResource: {e}")

        # Load global application styling (from resource bundle now)
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_resource('/com/taliskerman/klon/style.css')
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            logging.error(f"Failed to load CSS: {e}")

        # Register custom icons contained in the resource path
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_resource_path('/com/taliskerman/klon')
        
        # Add 'about' action to display the application description
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about_action)
        self.add_action(action)

    def on_about_action(self, action, param):
        """Callback to show the Libadwaita About dialog when triggered."""
        win = self.props.active_window
        if win:
            show_about_dialog(win)

def setup_logging():
    """Configure directory structure and logging patterns for the Klon runtime."""
    log_dir = os.path.expanduser("~/.cache/klon")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "klon.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logging.info("Klon Application Started")

def main():
    """Set up log configurations and execute the Adw application event loop."""
    setup_logging()
    app = KlonApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())

