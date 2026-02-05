import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from importlib.metadata import version, PackageNotFoundError
import sys
from pathlib import Path

def get_version():
    try:
        return version("klon")
    except PackageNotFoundError:
        # Fallback for dev environment or when package metadata is elusive
        try:
            with open(Path(__file__).parents[2] / "pyproject.toml") as f:
                for line in f:
                    if line.startswith('version = "'):
                        return line.split('"')[1]
        except:
            return "0.0.0-dev"
    return "0.2.0"

def show_about_dialog(parent):
    win = Adw.AboutWindow(transient_for=parent)
    win.set_application_name("Klon")
    win.set_application_icon("com.taliskerman.klon")
    win.set_developer_name("Chuck Talk")
    win.set_version(get_version())
    win.set_copyright("© 2026 Chuck Talk")
    win.set_website("https://chucktalk.com")
    win.set_issue_url("mailto:cwtalk1@gmail.com")
    win.set_license_type(Gtk.License.GPL_3_0)
    win.present()

