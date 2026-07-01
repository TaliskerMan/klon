"""Tests for the clone/backup/verify backend (P0-1, P2-11, P2-12).

The `dd` subprocess itself is mocked; these tests assert the *decisions* around
it: that backup targets a not-yet-existing image, that the dd invocation carries
the error-tolerant flags, and that read-back verification correctly compares
source and destination.
"""

import hashlib
import types

import pytest

from klon.backend import clone


class _FakeProc:
    """Minimal stand-in for a finished subprocess.Popen with empty stderr."""

    def __init__(self):
        self.returncode = 0
        self.stderr = types.SimpleNamespace(readline=lambda: "")

    def poll(self):
        return 0


@pytest.fixture
def captured_dd(monkeypatch):
    """Capture the argv dd would be launched with, and skip real validation."""
    calls = {}

    monkeypatch.setattr(clone, "validate_destructive_write", lambda *a, **k: None)
    monkeypatch.setattr(clone.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_popen(cmd, **kwargs):
        calls["cmd"] = cmd
        return _FakeProc()

    monkeypatch.setattr(clone.subprocess, "Popen", fake_popen)
    return calls


def test_clone_uses_error_tolerant_flags(captured_dd):
    clone.clone_drive("/dev/sda", "/dev/sdb")
    cmd = captured_dd["cmd"]
    assert "conv=fsync,noerror,sync" in cmd  # P2-11: survive read errors on failing media.
    assert "if=/dev/sda" in cmd and "of=/dev/sdb" in cmd
    # Invocation is array form (no shell string) — injection-safe invariant.
    assert isinstance(cmd, list)


def test_backup_to_image_targets_a_file_not_a_device(monkeypatch):
    """P0-1: backup must pass dest_is_device=False so a fresh path isn't rejected."""
    seen = {}
    monkeypatch.setattr(
        clone, "validate_destructive_write",
        lambda src, dst, **kw: seen.update(kw, src=src, dst=dst),
    )
    monkeypatch.setattr(clone.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(clone.subprocess, "Popen", lambda cmd, **kw: _FakeProc())

    clone.backup_to_image("/dev/sda", "/home/user/new-backup.img")
    assert seen["dest_is_device"] is False


def test_missing_binaries_raise(monkeypatch):
    monkeypatch.setattr(clone, "validate_destructive_write", lambda *a, **k: None)
    monkeypatch.setattr(clone.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="pkexec, dd"):
        clone.clone_drive("/dev/sda", "/dev/sdb")


def test_verify_clone_matches_identical_prefix(tmp_path, monkeypatch):
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    payload = b"klon-verify-payload" * 100
    src.write_bytes(payload)
    dst.write_bytes(payload + b"TRAILING-GARBAGE-IGNORED")  # Only prefix is compared.

    monkeypatch.setattr(clone, "source_size_bytes", lambda p: len(payload))
    assert clone.verify_clone(str(src), str(dst)) is True


def test_verify_clone_detects_corruption(tmp_path, monkeypatch):
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"A" * 500)
    dst.write_bytes(b"A" * 499 + b"B")

    monkeypatch.setattr(clone, "source_size_bytes", lambda p: 500)
    assert clone.verify_clone(str(src), str(dst)) is False
