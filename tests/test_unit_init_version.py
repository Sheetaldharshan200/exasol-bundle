"""
Unit tests for exasol_bundle/__init__.py dynamic version lookup.

Tests:
1. __version__ is a non-empty string when the package is installed (or fallback "0.0.0-dev")
2. Fallback "0.0.0-dev" returned when PackageNotFoundError is raised
3. Source uses importlib.metadata, not a hardcoded version literal
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
INIT_PATH = ROOT / "exasol_bundle" / "__init__.py"


def _reload_init(mock_version_fn=None):
    """
    Execute __init__.py in a fresh module context and return the resulting
    __version__ value. Optionally patch importlib.metadata.version.
    """
    source = INIT_PATH.read_text(encoding="utf-8")
    namespace: dict = {}
    if mock_version_fn is not None:
        # Provide a patched version of importlib.metadata inside the exec context
        import importlib.metadata as _meta
        import types
        fake_meta = types.ModuleType("importlib.metadata")
        fake_meta.version = mock_version_fn
        from importlib.metadata import PackageNotFoundError  # real exception class
        fake_meta.PackageNotFoundError = PackageNotFoundError
        with patch.dict(sys.modules, {"importlib.metadata": fake_meta}):
            exec(compile(source, str(INIT_PATH), "exec"), namespace)
    else:
        exec(compile(source, str(INIT_PATH), "exec"), namespace)
    return namespace.get("__version__")


# ---------------------------------------------------------------------------
# 1. __version__ is non-empty when package is installed (or fallback)
# ---------------------------------------------------------------------------

class TestVersionNonEmpty:
    """__version__ must always be a non-empty string."""

    def test_version_is_str(self):
        ver = _reload_init()
        assert isinstance(ver, str), f"__version__ must be a str, got {type(ver)}"

    def test_version_is_non_empty(self):
        ver = _reload_init()
        assert ver, "__version__ must be a non-empty string"

    def test_version_is_not_hardcoded_old_value(self):
        ver = _reload_init()
        assert ver != "1.0.4", (
            "__version__ should not be the old hardcoded '1.0.4' — "
            "it must come from importlib.metadata or the '0.0.0-dev' fallback"
        )


# ---------------------------------------------------------------------------
# 2. Fallback "0.0.0-dev" when PackageNotFoundError is raised
# ---------------------------------------------------------------------------

class TestFallbackVersion:
    """When the package is not installed, __version__ must be '0.0.0-dev'."""

    def test_fallback_is_0_0_0_dev(self):
        from importlib.metadata import PackageNotFoundError

        def raise_not_found(_):
            raise PackageNotFoundError("exasol-bundle")

        ver = _reload_init(mock_version_fn=raise_not_found)
        assert ver == "0.0.0-dev", (
            f"Expected fallback '0.0.0-dev' when PackageNotFoundError is raised, got {ver!r}"
        )


# ---------------------------------------------------------------------------
# 3. Source file uses importlib.metadata (not a hardcoded version string)
# ---------------------------------------------------------------------------

class TestSourceUsesImportlibMetadata:
    """The __init__.py source must use importlib.metadata and not a literal version."""

    def test_uses_importlib_metadata(self):
        source = INIT_PATH.read_text(encoding="utf-8")
        assert "importlib.metadata" in source, (
            "__init__.py must import from importlib.metadata for dynamic version lookup"
        )

    def test_no_hardcoded_version_literal(self):
        source = INIT_PATH.read_text(encoding="utf-8")
        import re
        # Should not contain __version__ = "x.y.z" with a numeric version
        hardcoded = re.search(r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']', source)
        assert hardcoded is None, (
            f"__init__.py must not contain a hardcoded version literal, "
            f"found: {hardcoded.group(0) if hardcoded else ''}"
        )

    def test_uses_version_function_call(self):
        source = INIT_PATH.read_text(encoding="utf-8")
        import re
        assert re.search(r'__version__\s*=\s*version\s*\(', source), (
            "__init__.py must assign __version__ via the version() function call"
        )
