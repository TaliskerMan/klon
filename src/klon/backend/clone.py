"""Disk cloning and raw image backup/restore wrapper.

This module executes `dd` as a subprocess with root privileges using `pkexec`
to clone physical block devices or save/restore them from raw file images.
It monitors the progress feedback written to the subprocess's stderr stream.

All destructive operations are validated by :mod:`klon.backend.safety` before
any data is written (mounted/root-disk refusal, capacity check, parent/child
rejection).
"""

import subprocess  # nosec B404
import shutil
import logging
import hashlib
import os

from .safety import validate_destructive_write, source_size_bytes


def clone_drive(
    source_path: str,
    dest_path: str,
    update_callback=None,
    *,
    dest_is_device: bool = True,
    allow_mounted_dest: bool = False,
):
    """Clones a source block device or image to a destination device or image.

    Runs `dd` with `status=progress` and `conv=fsync,noerror,sync` (the
    error-tolerant flags let a clone of failing media continue past read errors
    instead of aborting). Writing block devices needs root, so the command runs
    via `pkexec`.

    Args:
        source_path: Absolute path to the source device or raw disk image.
        dest_path: Absolute path to the destination device or target raw image.
        update_callback: Optional callable accepting a string for live status.
        dest_is_device: True if the destination is a block device; False if it's
            an image file (which `dd` will create — see P0-1).
        allow_mounted_dest: Explicit override to permit a non-root mounted
            destination (the GUI sets this only after a typed confirmation).

    Raises:
        UnsafeOperationError: If the operation is refused on safety grounds.
        RuntimeError: If pkexec or dd is missing from PATH, or if dd fails.
    """
    # Safety gate — refuses root/system disk, mounted dests (unless overridden),
    # oversize sources, and parent/child device pairs.
    validate_destructive_write(
        source_path,
        dest_path,
        dest_is_device=dest_is_device,
        allow_mounted_dest=allow_mounted_dest,
    )

    logging.info("Starting clone from %s to %s...", source_path, dest_path)

    pkexec_path = shutil.which('pkexec')
    dd_path = shutil.which('dd')
    if not pkexec_path or not dd_path:
        raise RuntimeError("Required binaries (pkexec, dd) not found in PATH")

    cmd = [
        pkexec_path,  # We need root privileges for block device access
        dd_path,
        f'if={source_path}',
        f'of={dest_path}',
        'bs=4M',
        'status=progress',
        'conv=fsync,noerror,sync',
    ]

    try:
        process = subprocess.Popen(  # nosec B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # dd outputs progress information to stderr
            text=True,
        )

        # Process stderr line by line to capture progress.
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                if update_callback:
                    update_callback(line.strip())
                else:
                    logging.info(line.strip())

        if process.returncode != 0:
            raise RuntimeError("Clone process failed")

        logging.info("Cloning completed successfully.")

    except Exception as error:
        logging.error("Cloning failed: %s", error)
        raise


def backup_to_image(source_device: str, image_path: str, update_callback=None):
    """Backs up a physical source device into a raw disk image file.

    The destination image does not need to exist — `dd` creates it (this fixes
    the P0-1 bug where a fresh `backup.img` path was wrongly rejected).

    Args:
        source_device: Absolute path to the source block device (e.g., /dev/sda).
        image_path: Absolute path to the destination image file (may be new).
        update_callback: Optional status callback to report live progress.
    """
    clone_drive(source_device, image_path, update_callback, dest_is_device=False)


def restore_from_image(
    image_path: str,
    dest_device: str,
    update_callback=None,
    *,
    allow_mounted_dest: bool = False,
):
    """Restores a raw disk image file back into a physical destination device.

    Args:
        image_path: Absolute path to the source raw disk image.
        dest_device: Absolute path to the target block device (e.g., /dev/sdb).
        update_callback: Optional status callback to report live progress.
        allow_mounted_dest: Explicit override for a non-root mounted destination.

    Raises:
        UnsafeOperationError: If the image is missing or the destination is unsafe.
    """
    clone_drive(
        image_path,
        dest_device,
        update_callback,
        dest_is_device=True,
        allow_mounted_dest=allow_mounted_dest,
    )


def verify_clone(source_path: str, dest_path: str, update_callback=None) -> bool:
    """Read-back verification: confirm the destination matches the source.

    Hashes `source_size` bytes from both source and destination with SHA-256 so
    a "Backup Complete!" message actually means the data matches (P2-12). For a
    device destination only the meaningful prefix (the source size) is compared.

    Returns:
        True if the hashes match, False otherwise.
    """
    size = source_size_bytes(source_path)

    def _hash_prefix(path: str, nbytes: int) -> str:
        h = hashlib.sha256()
        remaining = nbytes
        chunk = 4 * 1024 * 1024
        with open(path, 'rb') as f:
            while remaining > 0:
                buf = f.read(min(chunk, remaining))
                if not buf:
                    break
                h.update(buf)
                remaining -= len(buf)
        return h.hexdigest()

    if update_callback:
        update_callback("Verifying clone (reading back and comparing)...")
    try:
        src_hash = _hash_prefix(source_path, size)
        dst_hash = _hash_prefix(dest_path, size)
    except PermissionError:
        logging.warning("Verification needs read access to the device; skipped.")
        return False
    ok = src_hash == dst_hash
    logging.info("Clone verification %s", "passed" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    # Test stub - DO NOT RUN without valid args
    logging.warning("This module provides cloning functionality. Import it to use.")
