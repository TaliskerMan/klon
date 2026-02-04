# Klon Walkthrough

I have successfully initialized the `klon` project, implemented the core system cloning features, and generated the required packages.

## Artifacts Created

### Source Code
- **Repository**: `/home/freecode/antigrav/klon`
- **Main App**: `src/klon/main.py`
- **Core Logic**: `src/klon/backend/` (drives.py, clone.py)
- **GUI**: `src/klon/gui/` (window.py, about.py)

### Packages
- **DEB Package**: `/home/freecode/antigrav/klon_0.1.0-1_all.deb`
- **SHA512 Checksum**: `/home/freecode/antigrav/SHA512SUMS`
- **Flatpak Manifest**: `/home/freecode/antigrav/klon/com.taliskerman.klon.yml`

## Verification Steps

### 1. Identify Package
Check the SHA512 hash of the generated package:
```bash
sha512sum -c SHA512SUMS
```

### 2. Install DEB
You can install the package directly:
```bash
sudo dpkg -i klon_0.1.0-1_all.deb
sudo apt-get install -f # Fix dependencies if needed
```

### 3. Run Application
Launch from terminal or app grid:
```bash
klon
```

### 4. Cloning Test
To test cloning:
1. Open Klon.
2. Select a source drive (e.g. your OS drive).
3. Select a destination drive (e.g. an external USB).
4. Click "Start Cloning".
> [!WARNING]
> This operations is **destructive** to the destination drive.

## Licensing
The project is licensed under **GPLv3**.
Copyright © 2026 Chuck Talk <cwtalk1@gmail.com>
