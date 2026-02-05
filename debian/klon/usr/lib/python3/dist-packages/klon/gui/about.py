import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from importlib.metadata import version, PackageNotFoundError
import webbrowser
import sys
from pathlib import Path

def get_version():
    try:
        return version("klon")
    except PackageNotFoundError:
        # Fallback for dev environment
        try:
            with open(Path(__file__).parents[2] / "pyproject.toml") as f:
                for line in f:
                    if line.startswith('version = "'):
                        return line.split('"')[1]
        except:
            return "0.0.0-dev"

def show_license_dialog(parent):
    win = Adw.Window(transient_for=parent)
    win.set_title("License")
    win.set_default_size(600, 500)
    win.set_modal(True)
    
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    win.set_content(box)
    
    header = Adw.HeaderBar()
    box.append(header)
    
    scrolled = Gtk.ScrolledWindow()
    box.append(scrolled)
    scrolled.set_vexpand(True)
    
    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    text_view.set_left_margin(20)
    text_view.set_right_margin(20)
    text_view.set_top_margin(20)
    text_view.set_bottom_margin(20)
    scrolled.set_child(text_view)
    
    buffer = text_view.get_buffer()
    
    license_text = "Copyright (C) 2026 Chuck Talk\n\n"
    license_text += "This program is free software: you can redistribute it and/or modify "
    license_text += "it under the terms of the GNU General Public License as published by "
    license_text += "the Free Software Foundation, either version 3 of the License, or "
    license_text += "(at your option) any later version.\n\n"
    license_text += "This program is distributed in the hope that it will be useful, "
    license_text += "but WITHOUT ANY WARRANTY; without even the implied warranty of "
    license_text += "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
    license_text += "GNU General Public License for more details.\n\n"
    license_text += "You should have received a copy of the GNU General Public License "
    license_text += "along with this program.  If not, see <https://www.gnu.org/licenses/>."
    
    buffer.set_text(license_text)
    win.present()

def show_about_dialog(parent, app_name="Klon"):
    win = Adw.Window(transient_for=parent)
    win.set_title("About Klon")
    win.set_default_size(500, 400)
    win.set_modal(True)
    
    # Main Structure
    toolbar_view = Adw.ToolbarView()
    win.set_content(toolbar_view)
    
    header = Adw.HeaderBar()
    toolbar_view.add_top_bar(header)
    
    # Status Page for Content
    page = Adw.StatusPage()
    page.set_icon_name("com.taliskerman.klon")
    page.set_title("Klon")
    
    ver = get_version()
        
    page.set_description(f"System Cloning & Recovery Tool\nVersion {ver}\n\n© 2026 Chuck Talk")
    toolbar_view.set_content(page)
    
    # Action Box for Custom Buttons
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box.set_halign(Gtk.Align.CENTER)
    page.set_child(box)
    
    # Website Button
    btn_web = Gtk.Button()
    btn_web.set_icon_name("klon-website")
    btn_web.set_tooltip_text("Visit Website")
    btn_web.add_css_class("pill") # Clean look
    btn_web.set_size_request(64, 64) 
    btn_web.connect("clicked", lambda x: webbrowser.open("https://chucktalk.com"))
    box.append(btn_web)
    
    # Issue Button
    btn_issue = Gtk.Button()
    btn_issue.set_icon_name("klon-issue")
    btn_issue.set_tooltip_text("Report an Issue")
    btn_issue.add_css_class("pill")
    btn_issue.set_size_request(64, 64)
    btn_issue.connect("clicked", lambda x: webbrowser.open("mailto:cwtalk1@gmail.com"))
    box.append(btn_issue)
    
    # License Button
    btn_lic = Gtk.Button()
    btn_lic.set_icon_name("text-x-generic-symbolic") 
    btn_lic.set_tooltip_text("View License (GPLv3)")
    btn_lic.add_css_class("pill")
    btn_lic.set_size_request(64, 64)
    btn_lic.connect("clicked", lambda x: show_license_dialog(win))
    box.append(btn_lic)

    win.present()
