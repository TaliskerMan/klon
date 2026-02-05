import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from importlib.metadata import version
import webbrowser

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
    
    try:
        ver = version("klon")
    except:
        ver = "0.0.0-dev"
        
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
    btn_web.set_size_request(64, 64) # Make them bigish
    btn_web.connect("clicked", lambda x: webbrowser.open("https://github.com/chucktalk/klon"))
    box.append(btn_web)
    
    # Issue Button
    btn_issue = Gtk.Button()
    btn_issue.set_icon_name("klon-issue")
    btn_issue.set_tooltip_text("Report an Issue")
    btn_issue.add_css_class("pill")
    btn_issue.set_size_request(64, 64)
    btn_issue.connect("clicked", lambda x: webbrowser.open("https://github.com/chucktalk/klon/issues"))
    box.append(btn_issue)
    
    # License Button (Standard Icon)
    btn_lic = Gtk.Button()
    btn_lic.set_icon_name("text-x-generic-symbolic") # Standard icon for license
    btn_lic.set_tooltip_text("View License (GPLv3)")
    btn_lic.add_css_class("pill")
    btn_lic.set_size_request(64, 64)
    # Ideally show license text, but for now just open repo license
    btn_lic.connect("clicked", lambda x: webbrowser.open("https://github.com/chucktalk/klon/blob/main/LICENSE"))
    box.append(btn_lic)

    win.present()
