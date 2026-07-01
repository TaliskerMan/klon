"""Tests for the ISO resolver/downloader (P1-4, P1-5).

Network access is mocked. These assert the dynamic filename resolution (so a
point-release bump doesn't 404) and that a checksum mismatch is treated as a
failed download and the corrupt file is removed.
"""

import hashlib

import pytest

from klon.backend import iso


SUMS = """\
1111111111111111111111111111111111111111111111111111111111111111 *debian-live-12.0.0-amd64-standard.iso
2222222222222222222222222222222222222222222222222222222222222222 *debian-live-12.0.0-amd64-gnome.iso
"""


class _Resp:
    def __init__(self, text="", content=b"", status=200):
        self.text = text
        self._content = content
        self.status_code = status
        self.headers = {"content-length": str(len(content))}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise iso.requests.HTTPError(f"status {self.status_code}")

    def iter_content(self, block_size):
        for i in range(0, len(self._content), block_size):
            yield self._content[i:i + block_size]


def test_resolve_current_iso_picks_variant(monkeypatch):
    monkeypatch.setattr(iso.requests, "get", lambda url, timeout=None: _Resp(text=SUMS))
    url, name, sha = iso.resolve_current_iso("standard")
    assert name == "debian-live-12.0.0-amd64-standard.iso"
    assert url.endswith(name)
    assert sha == "1" * 64


def test_resolve_current_iso_raises_when_variant_absent(monkeypatch):
    monkeypatch.setattr(iso.requests, "get", lambda url, timeout=None: _Resp(text=SUMS))
    with pytest.raises(RuntimeError, match="No 'xfce' live ISO"):
        iso.resolve_current_iso("xfce")


def test_download_iso_verifies_good_checksum(tmp_path, monkeypatch):
    content = b"a-fake-iso-payload" * 1000
    good = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(
        iso.requests, "get",
        lambda url, stream=False, timeout=None: _Resp(content=content),
    )
    dest = tmp_path / "out.iso"
    ok = iso.download_iso("http://x/iso", str(dest), expected_sha256=good)
    assert ok is True
    assert dest.exists()


def test_download_iso_rejects_and_deletes_bad_checksum(tmp_path, monkeypatch):
    content = b"corrupt-bytes"
    monkeypatch.setattr(
        iso.requests, "get",
        lambda url, stream=False, timeout=None: _Resp(content=content),
    )
    dest = tmp_path / "out.iso"
    ok = iso.download_iso("http://x/iso", str(dest), expected_sha256="deadbeef" * 8)
    assert ok is False
    assert not dest.exists()  # Corrupt download must not be left behind for flashing.


def test_verify_iso(tmp_path):
    p = tmp_path / "f.iso"
    p.write_bytes(b"hello")
    assert iso.verify_iso(str(p), hashlib.sha256(b"hello").hexdigest()) is True
    assert iso.verify_iso(str(p), "0" * 64) is False
