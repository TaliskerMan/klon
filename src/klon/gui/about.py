"""Application description and licensing dialogue window.

This module implements the Adw.AboutWindow wrapper, showing author details, GPLv3
licensing terms, and dynamically parsing the version string from pyproject.toml
if package metadata is unavailable.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from importlib.metadata import version, PackageNotFoundError
import sys
import logging
from pathlib import Path

def get_version() -> str:
    """Retrieve the application version string.

    Tries to retrieve the version via importlib.metadata first. If the package is
    not installed (e.g., in development mode), it falls back to reading the
    pyproject.toml version field directly.

    Returns:
        The version string, defaulting to "0.0.0-dev" if parsing fails completely.
    """
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

def show_about_dialog(parent: Gtk.Window):
    """Instantiate and present the Adw.AboutWindow.

    Configures the application name, developer profile, GPL v3 licensing details,
    website links, and loads the com.taliskerman.klon icon texture.

    Args:
        parent: The transient parent Gtk Window.
    """
    window = Adw.AboutWindow(transient_for=parent)
    window.set_application_name("Klon")
    try:
        texture = Gdk.Texture.new_from_resource("/com/taliskerman/klon/hicolor/512x512/apps/klon-clone.png")
        # Ensure Adwaita version supports this (introduced in 1.2, but maybe earlier as paintable?)
        # Adw 1.0 might only have application-icon.
        # Let's try setting property directly if method is missing?
        if hasattr(window, "set_application_logo"):
            window.set_application_logo(texture)
        else:
            # Fallback: resource path sometimes works as icon name in older GTK?
            window.set_application_icon("com.taliskerman.klon") 
    except Exception as error:
        logging.error(f"Failed to set logo: {error}")
        window.set_application_icon("com.taliskerman.klon")
    
    window.set_developer_name("Chuck Talk")
    window.set_version(get_version())
    window.set_copyright("© 2026 Chuck Talk")
    window.set_website("https://chucktalk.com")
    window.set_issue_url("mailto:chuck@nordheim.online")
    window.set_license_type(Gtk.License.GPL_3_0)
    window.present()


