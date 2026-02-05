import sys
import os

# Create a dummy window class to mock the argument
class DummyWindow:
    pass

try:
    # Add src to path
    sys.path.insert(0, os.path.abspath("src"))
    
    print("Attempting to import IsoPage...")
    from klon.gui.pages.iso_page import IsoPage
    print("Import successful.")
    
    print("Attempting to instantiate IsoPage...")
    page = IsoPage(window=DummyWindow())
    print("Instantiation successful.")
    
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk
    
    if isinstance(page, Gtk.Box):
        print("Page is a Gtk.Box.")
    else:
        print(f"Page is {type(page)}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
