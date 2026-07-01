"""Shared pytest fixtures/paths for the klon test suite.

Adds ``src/`` to ``sys.path`` so the backend packages import without requiring
an editable install, and without importing the GTK GUI layer (the tests here
exercise pure backend logic with mocked subprocess/lsblk).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
