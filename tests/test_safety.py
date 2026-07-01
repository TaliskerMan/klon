"""Unit tests for the destructive-write safety guards (P0-2).

These are the guards that stand between the user and an irreversible `dd` onto
the wrong disk, so they are the most important thing in the project to test.
Every hardware query is monkeypatched, so the suite runs on any machine with no
real devices and never touches a block device.
"""

import pytest

from klon.backend import safety
from klon.backend.safety import UnsafeOperationError, validate_destructive_write


@pytest.fixture
def dev(tmp_path, monkeypatch):
    """A world where source/dest exist and every disk is a healthy block device.

    Individual tests override single helpers to simulate a specific hazard.
    """
    src = tmp_path / "src.img"
    src.write_bytes(b"\0" * 1024)

    monkeypatch.setattr(safety, "is_block_device", lambda p: p.startswith("/dev/"))
    monkeypatch.setattr(safety, "holds_root_filesystem", lambda p: False)
    monkeypatch.setattr(safety, "device_mountpoints", lambda p: [])
    monkeypatch.setattr(safety, "is_same_or_child", lambda a, b: False)
    monkeypatch.setattr(safety, "device_size_bytes", lambda p: 8 * 1024 ** 3)
    monkeypatch.setattr(safety, "source_size_bytes", lambda p: 1 * 1024 ** 3)
    return {"src": str(src)}


def test_allows_a_safe_device_write(dev):
    # Should not raise.
    validate_destructive_write(dev["src"], "/dev/sdb", dest_is_device=True)


def test_missing_source_is_refused(dev):
    with pytest.raises(UnsafeOperationError, match="does not exist"):
        validate_destructive_write("/nope/missing.img", "/dev/sdb", dest_is_device=True)


def test_refuses_root_disk(dev, monkeypatch):
    monkeypatch.setattr(safety, "holds_root_filesystem", lambda p: True)
    with pytest.raises(UnsafeOperationError, match="root"):
        validate_destructive_write(dev["src"], "/dev/sda", dest_is_device=True)


def test_refuses_same_or_child_device(dev, monkeypatch):
    monkeypatch.setattr(safety, "is_same_or_child", lambda a, b: True)
    with pytest.raises(UnsafeOperationError, match="same disk|partition"):
        validate_destructive_write(dev["src"], "/dev/sda1", dest_is_device=True)


def test_refuses_mounted_dest_without_override(dev, monkeypatch):
    monkeypatch.setattr(safety, "device_mountpoints", lambda p: ["/media/usb"])
    with pytest.raises(UnsafeOperationError, match="mounted"):
        validate_destructive_write(dev["src"], "/dev/sdb", dest_is_device=True)


def test_allows_mounted_dest_with_override(dev, monkeypatch):
    monkeypatch.setattr(safety, "device_mountpoints", lambda p: ["/media/usb"])
    # Explicit override -> allowed.
    validate_destructive_write(
        dev["src"], "/dev/sdb", dest_is_device=True, allow_mounted_dest=True
    )


def test_override_never_bypasses_root_guard(dev, monkeypatch):
    monkeypatch.setattr(safety, "holds_root_filesystem", lambda p: True)
    monkeypatch.setattr(safety, "device_mountpoints", lambda p: ["/"])
    with pytest.raises(UnsafeOperationError, match="root"):
        validate_destructive_write(
            dev["src"], "/dev/sda", dest_is_device=True, allow_mounted_dest=True
        )


def test_refuses_when_source_larger_than_dest(dev, monkeypatch):
    monkeypatch.setattr(safety, "source_size_bytes", lambda p: 16 * 1024 ** 3)
    monkeypatch.setattr(safety, "device_size_bytes", lambda p: 8 * 1024 ** 3)
    with pytest.raises(UnsafeOperationError, match="larger than destination"):
        validate_destructive_write(dev["src"], "/dev/sdb", dest_is_device=True)


def test_fails_safe_when_size_cannot_be_determined(dev, monkeypatch):
    def boom(_p):
        raise OSError("lsblk exploded")

    monkeypatch.setattr(safety, "device_size_bytes", boom)
    with pytest.raises(UnsafeOperationError, match="capacity"):
        validate_destructive_write(dev["src"], "/dev/sdb", dest_is_device=True)


def test_refuses_non_block_device_when_device_expected(dev, monkeypatch):
    monkeypatch.setattr(safety, "is_block_device", lambda p: False)
    with pytest.raises(UnsafeOperationError, match="not a block device"):
        validate_destructive_write(dev["src"], "/tmp/not-a-dev", dest_is_device=True)


# ── Image-file destination (backup) path ────────────────────────────────────

def test_image_dest_accepts_new_file_in_existing_dir(dev, tmp_path, monkeypatch):
    monkeypatch.setattr(safety, "is_block_device", lambda p: False)
    target = str(tmp_path / "backup.img")  # Does NOT exist yet — dd will create it.
    validate_destructive_write(dev["src"], target, dest_is_device=False)


def test_image_dest_refuses_missing_directory(dev):
    with pytest.raises(UnsafeOperationError, match="directory"):
        validate_destructive_write(
            dev["src"], "/no/such/dir/backup.img", dest_is_device=False
        )


def test_image_dest_refuses_a_block_device(dev, monkeypatch):
    monkeypatch.setattr(safety, "is_block_device", lambda p: True)
    with pytest.raises(UnsafeOperationError, match="block device"):
        validate_destructive_write(dev["src"], "/dev/sdb", dest_is_device=False)


# ── is_same_or_child name logic ─────────────────────────────────────────────

@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("/dev/sda", "/dev/sda", True),
        ("/dev/sda", "/dev/sda1", True),
        ("/dev/sda1", "/dev/sda", True),
        ("/dev/nvme0n1", "/dev/nvme0n1p2", True),
        ("/dev/sda", "/dev/sdb", False),
        ("/dev/sdb", "/dev/sda1", False),
    ],
)
def test_is_same_or_child(a, b, expected):
    assert safety.is_same_or_child(a, b) is expected
