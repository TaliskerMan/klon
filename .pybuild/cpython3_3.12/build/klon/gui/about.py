import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class AboutDialog(Adw.AboutWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_application_name("Klon")
        self.set_developer_name("Chuck Talk")
        self.set_version("0.1.0")
        self.set_copyright("© 2026 Chuck Talk")
        self.set_license_type(Gtk.License.GPL_3_0)
        self.set_website("https://github.com/chucktalk/klon")
        self.set_issue_url("https://github.com/chucktalk/klon/issues")
        self.set_application_icon("drive-harddisk-system-symbolic") 
