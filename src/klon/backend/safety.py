"""Safety guards for destructive disk operations.

klon writes raw block devices, so an unguarded destination can destroy the
running system. These helpers let the clone/restore paths refuse the most
dangerous mistakes BEFORE any `dd` runs:

* the destination is the running root/system disk (always refused);
* the destination (or one of its partitions) is mounted (refused unless the
  caller explicitly overrides after a strong confirmation);
* the source is larger than the destination (would abort mid-write);
* source and destination are the same device, or one is a child of the other
  (exception.g. /dev/sda vs /dev/sda1).

Everything here shells out via array-form subprocess (no shell) and is written
to be unit-testable by mocking `subprocess`/the small query helpers.
"""

import json
import logging
import os
import shutil
import subprocess  # nosec B404


class UnsafeOperationError(Exception):
    """Raised when a requested disk operation is refused on safety grounds."""


# ── Low-level queries (mock these in tests) ─────────────────────────────────

def is_block_device(path: str) -> bool:
    """True if *path* refers to an existing block device node."""
    try:
        import stat
        return stat.S_ISBLK(os.stat(path).st_mode)
    except OSError:
        return False


def _run_json(args: list) -> dict:
    result = subprocess.run(  # nosec B603
        args, capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def lsblk_device(path: str) -> dict:
    """Return lsblk JSON for a single device path (with mountpoints + size in bytes).

    The device node is normalized (`/dev/sda1` -> its parent disk is *not*
    resolved here; callers pass the exact node they care about).
    """
    lsblk = shutil.which("lsblk")
    if not lsblk:
        raise RuntimeError("lsblk not found in PATH")
    data = _run_json([lsblk, "-J", "-b", "-o", "NAME,PATH,SIZE,TYPE,MOUNTPOINT", path])
    devs = data.get("blockdevices", [])
    return devs[0] if devs else {}


def device_size_bytes(path: str) -> int:
    """Size of a block device in bytes (via lsblk -b)."""
    info = lsblk_device(path)
    return int(info.get("size") or 0)


def file_size_bytes(path: str) -> int:
    """Size of a regular file in bytes."""
    return os.path.getsize(path)


def source_size_bytes(path: str) -> int:
    """Size of a source that may be either a block device or an image file."""
    return device_size_bytes(path) if is_block_device(path) else file_size_bytes(path)


def _iter_mountpoints(node: dict):
    """Yield every mountpoint in a device and its children (recursively)."""
    mp = node.get("mountpoint")
    if mp:
        yield mp
    for child in node.get("children", []) or []:
        yield from _iter_mountpoints(child)


def device_mountpoints(path: str) -> list:
    """All mountpoints of *path* and its partitions (empty if none mounted)."""
    return list(_iter_mountpoints(lsblk_device(path)))


def holds_root_filesystem(path: str) -> bool:
    """True if *path* (or any of its partitions) currently holds `/`."""
    return "/" in device_mountpoints(path)


def is_same_or_child(a: str, b: str) -> bool:
    """True if a and b are the same device, or one is a partition of the other.

    Compares resolved kernel names so `/dev/sda` and `/dev/sda1` (and the
    reverse) are caught, as are symlinks like `/dev/disk/by-id/...`.
    """
    ra, rb = os.path.realpath(a), os.path.realpath(b)
    if ra == rb:
        return True
    na, nb = os.path.basename(ra), os.path.basename(rb)
    # exception.g. sda <-> sda1, nvme0n1 <-> nvme0n1p2, mmcblk0 <-> mmcblk0p1
    return nb.startswith(na) or na.startswith(nb)


# ── Orchestrator ────────────────────────────────────────────────────────────

def validate_destructive_write(
    source_path: str,
    dest_path: str,
    *,
    dest_is_device: bool,
    allow_mounted_dest: bool = False,
) -> None:
    if not os.path.exists(source_path):
        raise UnsafeOperationError(f"Source {source_path} does not exist.")

    if not dest_is_device:
        _validate_image_destination(dest_path)
        return

    if not is_block_device(dest_path):
        raise UnsafeOperationError(f"Destination {dest_path} is not a block device.")

    if holds_root_filesystem(dest_path):
        raise UnsafeOperationError(
            f"Refusing to write to {dest_path}: it holds the running root "
            f"filesystem (/). This would destroy your operating system."
        )

    if is_same_or_child(source_path, dest_path):
        raise UnsafeOperationError(
            f"Source ({source_path}) and destination ({dest_path}) are the "
            f"same disk or one is a partition of the other."
        )

    mounts = device_mountpoints(dest_path)
    if mounts and not allow_mounted_dest:
        raise UnsafeOperationError(
            f"Destination {dest_path} has mounted filesystem(s): "
            f"{', '.join(mounts)}. Unmount it, or confirm the override to "
            f"erase it."
        )

    _validate_capacity(source_path, dest_path)

def _validate_image_destination(dest_path: str) -> None:
    parent = os.path.dirname(os.path.abspath(dest_path)) or "."
    if not os.path.isdir(parent):
        raise UnsafeOperationError(
            f"Destination directory {parent} does not exist."
        )
    if is_block_device(dest_path):
        raise UnsafeOperationError(
            f"{dest_path} is a block device, not an image file."
        )

def _validate_capacity(source_path: str, dest_path: str) -> None:
    try:
        src = source_size_bytes(source_path)
        dst = device_size_bytes(dest_path)
        if src > dst:
            raise UnsafeOperationError(
                f"Source ({src} bytes) is larger than destination "
                f"({dst} bytes); the write would fail partway and leave an "
                f"unbootable target."
            )
    except UnsafeOperationError:
        raise
    except Exception as exception:
        logging.error("Could not determine device sizes: %s", exception)
        raise UnsafeOperationError(
            "Could not verify destination capacity; refusing to proceed."
        )
