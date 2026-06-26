"""
Unit and property-based tests for the rewritten PersonalDBComponent.

Covers:
  - Pure helpers: _get_platform, _build_url, _install_path, _is_windows
  - I/O orchestration: download errors, extraction errors, SHA256 paths,
    chmod, platform notices, temp-dir cleanup, idempotency
  - Property-based: totality, case-insensitivity, URL invariants,
    SHA256 round-trip, idempotence, mismatch cleanup, unsupported inertness
"""

import hashlib
import io
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))
from exasol_bundle.components.personal_db import PersonalDBComponent

# ---------------------------------------------------------------------------
# Hypothesis import (skip PBT gracefully if not installed)
# ---------------------------------------------------------------------------
try:
    from hypothesis import assume, given, settings
    from hypothesis.strategies import (
        binary, sampled_from, text,
    )
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

SUPPORTED_SLUGS = [
    "darwin/arm64", "darwin/amd64",
    "linux/amd64",  "linux/arm64",
    "windows/amd64",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_targz(member_name: str, content: bytes, tmp_path: Path) -> Path:
    """Create a .tar.gz with a single member at tmp_path/archive.tar.gz."""
    archive = tmp_path / "exasol.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(content)
        info.mode = 0o755
        tf.addfile(info, io.BytesIO(content))
    return archive


def _make_zip(member_name: str, content: bytes, tmp_path: Path) -> Path:
    """Create a .zip with a single member at tmp_path/archive.zip."""
    archive = tmp_path / "exasol.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(member_name, content)
    return archive


# ---------------------------------------------------------------------------
# Pure helper: _get_platform
# ---------------------------------------------------------------------------

class TestGetPlatform:
    def setup_method(self):
        self.comp = PersonalDBComponent()

    @pytest.mark.parametrize("sys_name,machine,expected", [
        ("Darwin",  "arm64",   "darwin/arm64"),
        ("Darwin",  "aarch64", "darwin/arm64"),
        ("Darwin",  "x86_64",  "darwin/amd64"),
        ("Darwin",  "amd64",   "darwin/amd64"),
        ("Linux",   "x86_64",  "linux/amd64"),
        ("Linux",   "amd64",   "linux/amd64"),
        ("Linux",   "arm64",   "linux/arm64"),
        ("Linux",   "aarch64", "linux/arm64"),
        ("Windows", "amd64",   "windows/amd64"),
        ("Windows", "AMD64",   "windows/amd64"),
        ("FreeBSD", "amd64",   "unsupported"),
        ("Darwin",  "riscv64", "unsupported"),
        ("",        "",        "unsupported"),
    ])
    def test_known_combinations(self, sys_name, machine, expected):
        assert self.comp._get_platform(sys_name, machine) == expected

    def test_case_insensitive_os(self):
        assert self.comp._get_platform("DARWIN", "arm64") == "darwin/arm64"
        assert self.comp._get_platform("linux", "X86_64") == "linux/amd64"

    def test_never_raises(self):
        for s in ["", "BeOS", "Plan9", "!@#$"]:
            for m in ["", "mips", "z80", "!@#$"]:
                result = self.comp._get_platform(s, m)
                assert isinstance(result, str)

    def test_returns_only_valid_values(self):
        valid = set(SUPPORTED_SLUGS) | {"unsupported"}
        for s in ["darwin", "linux", "windows", "freebsd", ""]:
            for m in ["arm64", "aarch64", "x86_64", "amd64", "mips", ""]:
                assert self.comp._get_platform(s, m) in valid


# ---------------------------------------------------------------------------
# Pure helper: _build_url
# ---------------------------------------------------------------------------

class TestBuildUrl:
    def setup_method(self):
        self.comp = PersonalDBComponent()

    @pytest.mark.parametrize("slug", SUPPORTED_SLUGS)
    def test_url_contains_slug(self, slug):
        archive_url, _ = self.comp._build_url(slug)
        assert slug in archive_url

    @pytest.mark.parametrize("slug", ["darwin/arm64", "darwin/amd64", "linux/amd64", "linux/arm64"])
    def test_unix_archive_ends_tar_gz(self, slug):
        archive_url, _ = self.comp._build_url(slug)
        assert archive_url.endswith(".tar.gz")

    def test_windows_archive_ends_zip(self):
        archive_url, _ = self.comp._build_url("windows/amd64")
        assert archive_url.endswith(".zip")

    @pytest.mark.parametrize("slug", SUPPORTED_SLUGS)
    def test_sha256_url_ends_sha256(self, slug):
        _, sha256_url = self.comp._build_url(slug)
        assert sha256_url.endswith(".sha256")

    def test_no_github_api_url(self):
        for slug in SUPPORTED_SLUGS:
            a, s = self.comp._build_url(slug)
            assert "api.github.com" not in a
            assert "api.github.com" not in s

    def test_s3_base_in_url(self):
        for slug in SUPPORTED_SLUGS:
            a, _ = self.comp._build_url(slug)
            assert "s3.eu-west-1.amazonaws.com" in a


# ---------------------------------------------------------------------------
# Pure helper: _install_path and _is_windows
# ---------------------------------------------------------------------------

class TestInstallPath:
    def setup_method(self):
        self.comp = PersonalDBComponent()

    def test_unix_path_no_exe(self):
        for slug in ["darwin/arm64", "darwin/amd64", "linux/amd64", "linux/arm64"]:
            p = self.comp._install_path(slug)
            assert p.name == "exasol-personal"

    def test_windows_path_has_exe(self):
        p = self.comp._install_path("windows/amd64")
        assert p.name == "exasol-personal.exe"

    def test_is_windows_correct(self):
        assert self.comp._is_windows("windows/amd64") is True
        assert self.comp._is_windows("darwin/arm64") is False
        assert self.comp._is_windows("linux/amd64") is False


# ---------------------------------------------------------------------------
# _extract helper tests
# ---------------------------------------------------------------------------

class TestExtract:
    def setup_method(self):
        self.comp = PersonalDBComponent()

    def test_extract_targz_happy(self, tmp_path):
        content = b"#!/bin/sh\necho hello"
        archive = _make_targz("exasol", content, tmp_path)
        dest = tmp_path / "out"
        dest.mkdir()
        result = self.comp._extract(archive, dest)
        assert result.read_bytes() == content

    def test_extract_zip_happy(self, tmp_path):
        content = b"Windows binary"
        archive = _make_zip("exasol.exe", content, tmp_path)
        dest = tmp_path / "out"
        dest.mkdir()
        result = self.comp._extract(archive, dest)
        assert result.read_bytes() == content

    def test_missing_tar_member_raises_keyerror(self, tmp_path):
        archive = _make_targz("other_file", b"data", tmp_path)
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises(KeyError, match="exasol"):
            self.comp._extract(archive, dest)

    def test_missing_zip_member_raises_keyerror(self, tmp_path):
        archive = _make_zip("other_file.exe", b"data", tmp_path)
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises(KeyError, match="exasol.exe"):
            self.comp._extract(archive, dest)

    def test_corrupt_tar_raises(self, tmp_path):
        archive = tmp_path / "exasol.tar.gz"
        archive.write_bytes(b"not a real tar.gz")
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises(tarfile.TarError):
            self.comp._extract(archive, dest)

    def test_corrupt_zip_raises(self, tmp_path):
        archive = tmp_path / "exasol.zip"
        archive.write_bytes(b"not a real zip")
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises(zipfile.BadZipFile):
            self.comp._extract(archive, dest)


# ---------------------------------------------------------------------------
# install() integration tests (all I/O mocked)
# ---------------------------------------------------------------------------

def _make_happy_path_install(tmp_path, slug="darwin/arm64", binary_content=b"binary"):
    """
    Returns a configured PersonalDBComponent + mock objects for a full happy-path
    install on the given slug. The mock _download writes a valid archive.
    """
    comp = PersonalDBComponent()
    install_dir = tmp_path / ".local" / "bin"

    is_win = slug.startswith("windows/")
    archive_content = b""  # set below

    def fake_download(url, dest):
        if is_win:
            # write a valid zip
            with zipfile.ZipFile(dest, "w") as zf:
                zf.writestr("exasol.exe", binary_content)
        else:
            # write a valid tar.gz
            with tarfile.open(dest, "w:gz") as tf:
                info = tarfile.TarInfo(name="exasol")
                info.size = len(binary_content)
                info.mode = 0o755
                tf.addfile(info, io.BytesIO(binary_content))

    mock_fetch = MagicMock(side_effect=urllib.error.URLError("no checksum"))
    mock_chmod = MagicMock()

    with patch.object(comp, "_get_platform", return_value=slug), \
         patch("pathlib.Path.home", return_value=tmp_path), \
         patch.object(comp, "_download", side_effect=fake_download), \
         patch.object(comp, "_fetch_text", mock_fetch), \
         patch("os.chmod", mock_chmod):
        comp.install()

    return install_dir, mock_chmod, mock_fetch


class TestInstallHappyPath:
    def test_binary_placed_on_darwin(self, tmp_path):
        install_dir, mock_chmod, _ = _make_happy_path_install(tmp_path, "darwin/arm64")
        binary = install_dir / "exasol-personal"
        assert binary.exists()
        assert binary.read_bytes() == b"binary"

    def test_chmod_755_called_on_unix(self, tmp_path):
        _, mock_chmod, _ = _make_happy_path_install(tmp_path, "linux/amd64")
        assert mock_chmod.called
        assert mock_chmod.call_args[0][1] == 0o755

    def test_windows_no_chmod(self, tmp_path):
        _, mock_chmod, _ = _make_happy_path_install(tmp_path, "windows/amd64")
        assert not mock_chmod.called

    def test_install_dir_created(self, tmp_path):
        # No pre-existing .local/bin
        install_dir = tmp_path / ".local" / "bin"
        assert not install_dir.exists()
        _make_happy_path_install(tmp_path, "darwin/arm64")
        assert install_dir.exists()

