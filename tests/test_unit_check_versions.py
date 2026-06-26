"""
Unit tests for scripts/check_versions.py

Tests cover:
  1. All four files at 1.0.18 → exit code 0
  2. package.json at 1.0.1 (others 1.0.18) → exit code 1, mentions npm-wrapper/package.json
  3. Homebrew formula at 1.0.16 (others 1.0.18) → exit code 1, mentions the formula file
  4. PKGBUILD at 1.0.16 (others 1.0.18) → exit code 1, mentions PKGBUILD
"""

import importlib.util
import sys
import io
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Load check_versions module from scripts/ at test-collection time
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "check_versions.py"


def _load_check_versions():
    """Import scripts/check_versions.py as a module object."""
    spec = importlib.util.spec_from_file_location("check_versions", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helpers to write temp versions of each file
# ---------------------------------------------------------------------------

def _write_pyproject(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "exasol-bundle"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def _write_package_json(root: Path, version: str) -> None:
    npm_dir = root / "npm-wrapper"
    npm_dir.mkdir(parents=True, exist_ok=True)
    (npm_dir / "package.json").write_text(
        f'{{"name": "exasol-bundle", "version": "{version}"}}\n',
        encoding="utf-8",
    )


def _write_homebrew(root: Path, version: str) -> None:
    formula_dir = root / "homebrew" / "Formula"
    formula_dir.mkdir(parents=True, exist_ok=True)
    (formula_dir / "exasol-bundle.rb").write_text(
        f'  url "https://files.pythonhosted.org/packages/source/e/exasol-bundle/'
        f'exasol-bundle-{version}.tar.gz"\n',
        encoding="utf-8",
    )


def _write_pkgbuild(root: Path, version: str) -> None:
    arch_dir = root / "arch-linux"
    arch_dir.mkdir(parents=True, exist_ok=True)
    (arch_dir / "PKGBUILD").write_text(
        f"pkgname=exasol-bundle\npkgver={version}\npkgrel=1\n",
        encoding="utf-8",
    )


def _write_all(root: Path, pyproject="1.0.18", npm="1.0.18", brew="1.0.18", pkg="1.0.18"):
    _write_pyproject(root, pyproject)
    _write_package_json(root, npm)
    _write_homebrew(root, brew)
    _write_pkgbuild(root, pkg)


# ---------------------------------------------------------------------------
# Fixture: fresh module instance patched to use a tmp directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def cv_module(tmp_path):
    """
    Load a fresh copy of check_versions and patch its ROOT to tmp_path so
    every file read goes to our temp directory instead of the real repo.
    """
    mod = _load_check_versions()
    with patch.object(mod, "ROOT", tmp_path):
        yield mod, tmp_path


# ---------------------------------------------------------------------------
# Test 1 — All four files at 1.0.18 → exit 0
# ---------------------------------------------------------------------------

class TestAllVersionsMatch:
    """All four static files report 1.0.18 → main() returns 0."""

    def test_exit_code_is_0_when_all_versions_match(self, cv_module):
        mod, root = cv_module
        _write_all(root)

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = mod.main()

        assert result == 0, (
            f"Expected exit code 0 when all versions match, got {result}.\n"
            f"Output:\n{captured.getvalue()}"
        )

    def test_output_says_ok_when_all_versions_match(self, cv_module):
        mod, root = cv_module
        _write_all(root)

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "[OK]" in output, (
            f"Expected '[OK]' in output when all versions match.\nOutput:\n{output}"
        )


# ---------------------------------------------------------------------------
# Test 2 — package.json at 1.0.1 (others 1.0.18) → exit 1, mentions file
# ---------------------------------------------------------------------------

class TestNpmVersionMismatch:
    """npm-wrapper/package.json at 1.0.1 while others are 1.0.18."""

    def test_exit_code_is_1_when_npm_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, npm="1.0.1")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = mod.main()

        assert result == 1, (
            f"Expected exit code 1 for npm version mismatch, got {result}.\n"
            f"Output:\n{captured.getvalue()}"
        )

    def test_output_mentions_package_json_when_npm_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, npm="1.0.1")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "npm-wrapper/package.json" in output, (
            f"Expected 'npm-wrapper/package.json' in output for npm mismatch.\nOutput:\n{output}"
        )

    def test_output_shows_mismatched_version_when_npm_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, npm="1.0.1")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "1.0.1" in output, (
            f"Expected '1.0.1' (the mismatched version) in output.\nOutput:\n{output}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Homebrew formula at 1.0.16 (others 1.0.18) → exit 1, mentions file
# ---------------------------------------------------------------------------

class TestHomebrewVersionMismatch:
    """homebrew/Formula/exasol-bundle.rb at 1.0.16 while others are 1.0.18."""

    def test_exit_code_is_1_when_homebrew_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, brew="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = mod.main()

        assert result == 1, (
            f"Expected exit code 1 for Homebrew version mismatch, got {result}.\n"
            f"Output:\n{captured.getvalue()}"
        )

    def test_output_mentions_homebrew_formula_when_brew_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, brew="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "homebrew/Formula/exasol-bundle.rb" in output, (
            f"Expected 'homebrew/Formula/exasol-bundle.rb' in output for brew mismatch.\nOutput:\n{output}"
        )

    def test_output_shows_mismatched_version_when_brew_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, brew="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "1.0.16" in output, (
            f"Expected '1.0.16' (the mismatched version) in output.\nOutput:\n{output}"
        )


# ---------------------------------------------------------------------------
# Test 4 — PKGBUILD at 1.0.16 (others 1.0.18) → exit 1, mentions PKGBUILD
# ---------------------------------------------------------------------------

class TestPkgbuildVersionMismatch:
    """arch-linux/PKGBUILD at 1.0.16 while others are 1.0.18."""

    def test_exit_code_is_1_when_pkgbuild_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, pkg="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = mod.main()

        assert result == 1, (
            f"Expected exit code 1 for PKGBUILD version mismatch, got {result}.\n"
            f"Output:\n{captured.getvalue()}"
        )

    def test_output_mentions_pkgbuild_when_pkgbuild_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, pkg="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "arch-linux/PKGBUILD" in output, (
            f"Expected 'arch-linux/PKGBUILD' in output for PKGBUILD mismatch.\nOutput:\n{output}"
        )

    def test_output_shows_mismatched_version_when_pkgbuild_mismatches(self, cv_module):
        mod, root = cv_module
        _write_all(root, pkg="1.0.16")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            mod.main()

        output = captured.getvalue()
        assert "1.0.16" in output, (
            f"Expected '1.0.16' (the mismatched version) in output.\nOutput:\n{output}"
        )
