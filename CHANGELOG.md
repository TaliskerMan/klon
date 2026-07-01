# Changelog — Klon

All notable changes to the Klon project are documented in this file. This project adheres to Semantic Versioning.

---

## [0.3.0] - 2026-07-01

### Added
- **Destructive-write safety guards** (`backend/safety.py`): every clone/restore/flash
  is validated before any `dd` runs. Always refuses the running root/system disk;
  refuses same/child devices, oversized sources, and mounted destinations unless the
  user explicitly confirms the override. Fails safe if device sizes can't be read.
- **Clone verification:** after a disk-to-disk clone, the destination is read back and
  compared to the source by SHA-256, and the result is surfaced in the UI.
- **ISO integrity:** the Debian Live ISO filename is now resolved dynamically from
  Debian's `SHA256SUMS` (no more hardcoded, soon-to-404 URL), downloads use connect/read
  timeouts, and the finished image is SHA-256 verified — a corrupt download is deleted
  rather than flashed.
- **Real persistence partition:** recovery USBs can now create an actual ext4
  `persistence` partition (sgdisk + mkfs.ext4 + `persistence.conf`) instead of the
  previous no-op. A persistence failure is reported distinctly from a flash failure.
- **Backend test suite** (`tests/`, pytest): covers the safety guards, backup/verify
  paths, and ISO resolution/checksum logic; runs with no hardware and no GTK.
- **Continuous integration:** GitHub Actions runs the test suite on push/PR.

### Fixed
- **Backup-to-image** no longer rejects a not-yet-existing target image file (P0-1).
- `dd` clones now use `conv=fsync,noerror,sync` so a clone of failing media continues
  past read errors instead of aborting.

### Changed
- Device pickers now show each disk's current mountpoint(s).
- Corrected maintainer email and repository homepage; re-scoped the Snyk audit note to
  state clearly that a clean automated scan is not a safety sign-off.
- Untracked build artifacts (`.deb`/`.sha512`, debhelper output, `.DS_Store`).

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
