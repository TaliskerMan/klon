import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw

class KlonApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.taliskerman.klon',
                         flags=0)

    def do_activate(self):
        window = Adw.ApplicationWindow(application=self)
        window.set_title("Klon")
        window.set_default_size(800, 600)

        content = Adw.StatusPage()
        content.set_title("Welcome to Klon")
        content.set_description("System Cloning & Recovery Tool")
        content.set_icon_name("drive-harddisk-system-symbolic")

        window.set_content(content)
        window.present()

def main():
    app = KlonApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
