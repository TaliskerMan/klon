# Klon

**Klon** is a system cloning and recovery tool designed for Pop!_OS (and other GNOME-based distributions). It allows users to create complete clones of their OS drives for emergency restoration and create bootable recovery media.

## Features

- **Full System Clone**: Copy an entire disk to another disk (`dd`-based), with read-back SHA-256 verification.
- **Image Backup & Restore**: Save a disk to a raw image file and restore it later.
- **Bootable Recovery Media**: Download the current Debian Live ISO (resolved dynamically and SHA-256 verified against Debian's published `SHA256SUMS`) and write it to a USB drive, optionally creating a real `persistence` partition.
- **User Friendly**: Simple GTK4 + Libadwaita interface.

## Safety

klon writes raw block devices, which is irreversible. Before any write it:

- **always refuses** the running root/system disk;
- refuses a destination smaller than the source, or that is the same disk as (or a partition of) the source;
- refuses a destination with mounted filesystems unless you explicitly confirm the override in the dialog;
- shows each disk's current mountpoint(s) in the device pickers so you can see what is in use.

Even so, **you are responsible for choosing the correct target.** Double-check the device before confirming.

## Requirements

Runtime tools invoked via `pkexec`: `dd`, `lsblk`, `partprobe`. Persistence additionally requires `sgdisk` (gdisk) and `mkfs.ext4` (e2fsprogs).

## Development

Run the backend test suite (no hardware or GTK required — all device access is mocked):

```
pip install -e '.[test]'
pytest
```

## License

This project is licensed under the GNU General Public License v3 or later (GPLv3+).
Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>

See the [LICENSE](LICENSE) file for details.
