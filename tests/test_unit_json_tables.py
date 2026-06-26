"""
Unit tests for JsonTablesComponent.
"""

import sys
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Import subject under test
# ---------------------------------------------------------------------------

from exasol_bundle.components.json_tables import JsonTablesComponent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def component():
    return JsonTablesComponent()


# ---------------------------------------------------------------------------
# Tests: install() — exasol_json_tables IS importable
# ---------------------------------------------------------------------------


class TestInstallWhenImportSucceeds:
    def test_prints_installed_message(self, component, capsys):
        """When exasol_json_tables imports successfully, output contains 'installed'."""
        import types

        fake_module = types.ModuleType("exasol_json_tables")
        with patch.dict(sys.modules, {"exasol_json_tables": fake_module}):
            component.install()

        captured = capsys.readouterr()
        assert "installed" in captured.out.lower()

    def test_does_not_raise(self, component):
        """install() must complete without raising any exception."""
        import types

        fake_module = types.ModuleType("exasol_json_tables")
        with patch.dict(sys.modules, {"exasol_json_tables": fake_module}):
            # Should not raise
            component.install()


# ---------------------------------------------------------------------------
# Tests: install() — exasol_json_tables is NOT importable
# ---------------------------------------------------------------------------


class TestInstallWhenImportFails:
    def test_prints_error_message(self, component, capsys):
        """When exasol_json_tables is missing, output contains '[ERROR]'."""
        # Remove from sys.modules if cached, then force ImportError via builtins
        sys.modules.pop("exasol_json_tables", None)

        with patch.dict(sys.modules, {"exasol_json_tables": None}):
            component.install()

        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out

    def test_does_not_raise(self, component):
        """install() must NOT propagate an ImportError — it catches it internally."""
        sys.modules.pop("exasol_json_tables", None)

        with patch.dict(sys.modules, {"exasol_json_tables": None}):
            # Should not raise even though the import will fail
            component.install()


# ---------------------------------------------------------------------------
# Tests: class structure
# ---------------------------------------------------------------------------


class TestClassStructure:
    def test_get_wheel_name_does_not_exist(self):
        """_get_wheel_name must NOT exist on the fixed JsonTablesComponent class."""
        assert not hasattr(JsonTablesComponent, "_get_wheel_name"), (
            "JsonTablesComponent still has _get_wheel_name — over-engineered "
            "wheel download logic was not removed."
        )

    def test_name_property_returns_json_tables(self, component):
        """The name property must return 'json-tables'."""
        assert component.name == "json-tables"
