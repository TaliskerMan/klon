# Changelog — Klon

All notable changes to the Klon project are documented in this file. This project adheres to Semantic Versioning.

---

## [0.2.9] - 2026-03-29

### Added
- **Release pipeline checks:** Aligned automatic package creation rules and version configurations using GPG signing.

---

## [0.2.5] - [0.2.8] - 2026-03-27

### Added
- **Incremental Release bumps:** Maintained version numbers synchronization with the Debian changelog files.

---

## [0.2.4] - 2026-02-08

### Added
- **Stable release build:** Official beta releases build.

---

## [0.2.3] - 2026-02-04

### Fixed
- **IsoPage Dropdown Error:** Fixed `AttributeError` in the Recovery USB setup view where variables mismatched (`target_dropdown` vs `dest_dropdown`).

---

## [0.2.2] - 2026-02-04

### Fixed
- **Recovery Page UI Crash:** Fixed Gtk Box crashes by removing direct nested `ActionRow` widgets from the Recovery USB page wrapper.

---

## [0.2.1] - 2026-02-04

### Fixed
- **Restore page crash:** Fixed missing page views and resolved Gtk layout sizing exceptions.

---

## [0.2.0] - 2026-02-04

### Changed
- **UI & Sizing Redesign:** Replaced custom icons tabs with text-only bold tabs.
- **Identity branding:** Centered large branding icons at the bottom of all view layers.
- **About dialog updates:** Added dynamic version lookup and local license text display.

---

## [0.1.5] - [0.1.9] - 2026-02-04

### Added
- **Icon Cache Refresh:** Added post-installation (`postinst`) script logic to trigger automatic update icon cache.
- **Aesthetic adjustments:** Repaired icon transparency (circular crop format), changed action buttons to PNGs, and adjusted About links.

---

## [0.1.2] - 2026-02-04

### Fixed
- **Startup Exception:** Fixed GApplication chaining errors causing instant crashes on workstation start.

---

## [0.1.1] - 2026-02-04

### Fixed
- **About page crash:** Repaired dialog layout logic.
- **Desktop launcher:** Created desktop launchers and added `requests` runtime dependencies.

---

## [0.1.0] - 2026-02-04

### Added
- **Initial release:** Minimal system cloning and emergency recovery tool designed in PyGObject (GTK4 + Libadwaita).
