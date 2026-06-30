"""Live ISO downloader and flashing wrapper.

Downloads a Debian Live ISO, verifies it against Debian's published
SHA256SUMS, and flashes it to a removable block device via `pkexec dd`. It can
optionally add a real persistence partition in the free space after the ISO
layout.
"""

import subprocess  # nosec B404
import shutil
import logging
import os
import hashlib
import tempfile
import requests

from .safety import validate_destructive_write, device_mountpoints


class PersistenceError(Exception):
    """Raised when the bootable flash succeeded but persistence setup failed."""


# Debian Live "current" directory. The exact ISO filename moves with each point
# release, so we resolve it dynamically from SHA256SUMS (see resolve_current_iso).
LIVE_DIR_URL = "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/"
DEFAULT_ISO_NAME = "debian-live-standard.iso"

# Network timeouts: (connect, read) seconds.
_TIMEOUT = (15, 120)


def resolve_current_iso(variant: str = "standard") -> tuple:
    """Resolve the current Debian Live ISO URL, filename, and SHA-256.

    Parses the SHA256SUMS in the live directory and picks the *-<variant>.iso
    entry. This avoids hardcoding a point-release filename that will 404 when
    Debian ships the next release (P1-5).

    Returns:
        (url, filename, sha256_hex)

    Raises:
        RuntimeError: if the sums can't be fetched or no matching ISO is found.
    """
    try:
        resp = requests.get(LIVE_DIR_URL + "SHA256SUMS", timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Could not fetch Debian SHA256SUMS: {error}") from error

    for line in resp.text.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, name = parts
        name = name.lstrip("*")
        if name.endswith(".iso") and f"-{variant}." in name:
            return (LIVE_DIR_URL + name, name, sha)
    raise RuntimeError(f"No '{variant}' live ISO found in current SHA256SUMS.")


def download_iso(url: str, dest_path: str, progress_callback=None,
                 expected_sha256: str | None = None) -> bool:
    """Download an ISO to *dest_path*, optionally verifying its SHA-256.

    Adds a connect/read timeout so a stalled connection can't hang forever
    (P1-4), and verifies the completed download against [expected_sha256] before
    returning success, so a truncated/corrupt image is never flashed.

    Returns:
        True only if the download (and any verification) succeeded.
    """
    try:
        response = requests.get(url, stream=True, timeout=_TIMEOUT)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 256
        downloaded = 0
        sha = hashlib.sha256()

        with open(dest_path, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                sha.update(data)
                downloaded += len(data)
                if progress_callback and total_size > 0:
                    percent = (downloaded / total_size) * 100
                    progress_callback(percent, f"Downloading: {int(percent)}%")
    except requests.RequestException as error:
        logging.error("Download error: %s", error)
        return False
    except OSError as error:
        logging.error("Could not write ISO: %s", error)
        return False

    if expected_sha256:
        return _verify_iso_checksum(dest_path, expected_sha256, progress_callback)
    return True

def _verify_iso_checksum(dest_path: str, expected_sha256: str, progress_callback=None) -> bool:
    sha = hashlib.sha256()
    with open(dest_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 256), b''):
            sha.update(chunk)
            
    actual = sha.hexdigest()
    if actual.lower() != expected_sha256.lower():
        logging.error("ISO checksum mismatch: expected %s, got %s",
                      expected_sha256, actual)
        if progress_callback:
            progress_callback(100, "Checksum FAILED — download is corrupt.")
        try:
            os.remove(dest_path)
        except OSError:
            pass
        return False
    if progress_callback:
        progress_callback(100, "Download verified (SHA-256 OK).")
    return True


def verify_iso(iso_path: str, expected_sha256: str) -> bool:
    """Verify an already-downloaded ISO against an expected SHA-256."""
    sha = hashlib.sha256()
    with open(iso_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 256), b''):
            sha.update(chunk)
    return sha.hexdigest().lower() == expected_sha256.lower()


def flash_iso_and_setup_persistence(
    iso_path: str,
    device_path: str,
    progress_callback=None,
    *,
    enable_persistence: bool = False,
    allow_mounted_dest: bool = False,
):
    """Flash a local ISO to a target USB device, optionally adding persistence.

    WARNING: destructive — completely overwrites the target device.

    Args:
        iso_path: Absolute path to the source ISO image.
        device_path: Absolute path to the destination USB device node.
        progress_callback: Optional (percent|None, message) callback.
        enable_persistence: If True, create a real persistence partition in the
            free space after flashing.
        allow_mounted_dest: Explicit override for a non-root mounted destination.

    Raises:
        ValueError: If the ISO file does not exist.
        UnsafeOperationError: If the destination fails the safety checks.
        RuntimeError: If required binaries are missing or an operation fails.
    """
    if not os.path.exists(iso_path):
        raise ValueError("ISO file not found")

    # Same destructive-write guards as cloning: never the root disk, etc.
    validate_destructive_write(
        iso_path, device_path, dest_is_device=True,
        allow_mounted_dest=allow_mounted_dest,
    )

    pkexec_path = shutil.which('pkexec')
    dd_path = shutil.which('dd')
    if not pkexec_path or not dd_path:
        raise RuntimeError("Required binaries (pkexec, dd) not found in PATH")

    if progress_callback:
        progress_callback(0, "Starting Flash operations...")

    _flash_image_to_drive(iso_path, device_path, pkexec_path, dd_path, progress_callback)

    # Reload the partition table so the kernel sees the new layout.
    partprobe_path = shutil.which("partprobe")
    if partprobe_path:
        subprocess.run([pkexec_path, partprobe_path, device_path], check=False)  # nosec B603

    if enable_persistence:
        if progress_callback:
            progress_callback(90, "Flashing complete. Creating persistence partition...")
        try:
            _setup_persistence_partition(device_path, pkexec_path, progress_callback)
        except Exception as e:
            # The bootable USB is already written; report persistence failure
            # distinctly so the caller doesn't treat the whole flash as failed.
            raise PersistenceError(str(e)) from e

    if progress_callback:
        progress_callback(100, "Done!")

def _flash_image_to_drive(iso_path: str, device_path: str, pkexec_path: str, dd_path: str, progress_callback=None):
    cmd = [
        pkexec_path, dd_path,
        f'if={iso_path}', f'of={device_path}',
        'bs=4M', 'status=progress', 'conv=fsync',
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  # nosec B603
    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line and progress_callback:
            progress_callback(None, f"Flashing: {line.strip()}")
    if process.returncode != 0:
        raise RuntimeError("Flashing failed")


def _partition_paths(device_path: str) -> set:
    """Return the set of child partition device paths for a disk (via lsblk)."""
    lsblk = shutil.which("lsblk")
    if not lsblk:
        return set()
    import json
    subprocess_result = subprocess.run(  # nosec B603
        [lsblk, "-J", "-o", "PATH,TYPE", device_path],
        capture_output=True, text=True, check=False,
    )
    try:
        data = json.loads(subprocess_result.stdout)
    except json.JSONDecodeError:
        return set()
    paths = set()
    for dev in data.get("blockdevices", []):
        for child in dev.get("children", []) or []:
            if child.get("path"):
                paths.add(child["path"])
    return paths


def _setup_persistence_partition(device_path, pkexec_path, progress_callback=None):
    """Create a real ext4 'persistence' partition in the free space (P1-6).

    Uses sgdisk to claim the largest free block, formats it ext4 labeled
    `persistence`, and writes a `persistence.conf` (`/ union`) so Debian Live
    actually persists changes. Fails loudly rather than swallowing errors.
    """
    sgdisk = shutil.which("sgdisk")
    mkfs = shutil.which("mkfs.ext4")
    if not sgdisk or not mkfs:
        raise RuntimeError(
            "Persistence requires 'sgdisk' (gdisk) and 'mkfs.ext4' (e2fsprogs); "
            "install them or disable persistence."
        )

    before = _partition_paths(device_path)

    # --new=0:0:0 -> next partition number, first free sector .. last free sector.
    res = subprocess.run(  # nosec B603
        [pkexec_path, sgdisk, "--new=0:0:0", "--typecode=0:8300",
         "--change-name=0:persistence", device_path],
        capture_output=True, text=True, check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"sgdisk failed to create persistence partition: {res.stderr.strip()}")

    partprobe = shutil.which("partprobe")
    if partprobe:
        subprocess.run([pkexec_path, partprobe, device_path], check=False)  # nosec B603

    after = _partition_paths(device_path)
    new_parts = sorted(after - before)
    if not new_parts:
        raise RuntimeError("Persistence partition was not created (no new partition detected).")
    part = new_parts[-1]

    # Format ext4 with the label Debian Live looks for.
    res = subprocess.run(  # nosec B603
        [pkexec_path, mkfs, "-L", "persistence", part],
        capture_output=True, text=True, check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"mkfs.ext4 failed on {part}: {res.stderr.strip()}")

    # Mount it and drop in persistence.conf ('/ union').
    mount = shutil.which("mount")
    umount = shutil.which("umount")
    if not mount or not umount:
        raise RuntimeError("mount/umount not found; cannot finalize persistence.conf.")

    with tempfile.TemporaryDirectory() as mnt:
        res = subprocess.run([pkexec_path, mount, part, mnt], capture_output=True, text=True, check=False)  # nosec B603
        if res.returncode != 0:
            raise RuntimeError(f"Could not mount {part}: {res.stderr.strip()}")
        try:
            conf = os.path.join(mnt, "persistence.conf")
            # Write via a privileged tee since the mount is root-owned.
            tee = shutil.which("tee")
            subprocess.run(  # nosec B603
                [pkexec_path, tee, conf],
                input="/ union\n", text=True, capture_output=True, check=True,
            )
        finally:
            subprocess.run([pkexec_path, umount, mnt], check=False)  # nosec B603

    if progress_callback:
        progress_callback(98, "Persistence partition created.")


def is_destination_mounted(device_path: str) -> bool:
    """Convenience for the GUI: does the chosen device have mounted partitions?"""
    try:
        return bool(device_mountpoints(device_path))
    except Exception:
        return False
