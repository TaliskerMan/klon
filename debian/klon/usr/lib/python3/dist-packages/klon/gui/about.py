import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from importlib.metadata import version

def show_about_dialog(parent, app_name="Klon"):
    about = Adw.AboutWindow(transient_for=parent)
    about.set_application_name(app_name)
    about.set_developer_name("Chuck Talk")
    try:
        about.set_version(version("klon"))
    except:
        about.set_version("0.0.0-dev")
    about.set_copyright("© 2026 Chuck Talk")
    about.set_license_type(Gtk.License.GPL_3_0)
    about.set_website("https://github.com/chucktalk/klon")
    about.set_issue_url("https://github.com/chucktalk/klon/issues")
    about.set_application_icon("com.taliskerman.klon")
    about.present() 
