"""
Source-analysis unit tests for npm-wrapper/bin/wrapper.js.

These tests read the JavaScript source and assert structural properties
about the Windows branch behaviour.
"""

import pathlib
import re

WRAPPER_PATH = pathlib.Path(__file__).parent.parent / "npm-wrapper" / "bin" / "wrapper.js"


def read_source() -> str:
    return WRAPPER_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Windows-no-Python exits with code 1 (and never exits with code 0)
# ---------------------------------------------------------------------------

class TestWindowsNoPythonExitCode:
    """process.exit(1) must appear in the Windows/no-Python path; process.exit(0) must not exist at all."""

    def test_process_exit_1_present(self):
        source = read_source()
        assert "process.exit(1)" in source, (
            "Expected process.exit(1) in wrapper.js (Windows/no-Python exit path)"
        )

    def test_process_exit_0_absent(self):
        source = read_source()
        assert "process.exit(0)" not in source, (
            "process.exit(0) should not appear anywhere in wrapper.js"
        )

    def test_exit_1_follows_install_python_windows_call(self):
        """process.exit(1) must appear after the installPythonWindows() call site."""
        source = read_source()
        install_call_pos = source.find("installPythonWindows()")
        assert install_call_pos != -1, "installPythonWindows() call not found"
        exit_1_pos = source.find("process.exit(1)", install_call_pos)
        assert exit_1_pos != -1, (
            "process.exit(1) not found after installPythonWindows() call"
        )


# ---------------------------------------------------------------------------
# 2. Restart / re-run message present
# ---------------------------------------------------------------------------

class TestRestartMessage:
    """The wrapper must tell the user to restart their terminal and re-run."""

    def test_restart_mentioned(self):
        source = read_source().lower()
        assert "restart" in source, "Expected 'restart' in wrapper.js output messages"

    def test_terminal_mentioned(self):
        source = read_source().lower()
        assert "terminal" in source, "Expected 'terminal' in wrapper.js output messages"

    def test_rerun_mentioned(self):
        source = read_source().lower()
        assert "re-run" in source, "Expected 're-run' in wrapper.js output messages"


# ---------------------------------------------------------------------------
# 3. Windows-with-Python proceeds to installer (checkCommand('uv') present)
# ---------------------------------------------------------------------------

class TestWindowsWithPythonProceeds:
    """After the python-absent guard block the happy path must check for 'uv'."""

    def test_check_command_uv_present(self):
        source = read_source()
        assert "checkCommand('uv')" in source, (
            "Expected checkCommand('uv') in wrapper.js happy-path installer block"
        )

    def test_check_command_uv_after_guard_block(self):
        """checkCommand('uv') must appear after the isWindows guard block."""
        source = read_source()
        # The guard block ends when we fall through to the pyCmd assignment
        guard_end_marker = "const pyCmd ="
        guard_end_pos = source.find(guard_end_marker)
        assert guard_end_pos != -1, f"Marker '{guard_end_marker}' not found in wrapper.js"

        uv_pos = source.find("checkCommand('uv')", guard_end_pos)
        assert uv_pos != -1, (
            "checkCommand('uv') not found after the python-absent guard block"
        )


# ---------------------------------------------------------------------------
# 4. `exa-bundle init` called in success path
# ---------------------------------------------------------------------------

class TestExaBundleInitCalled:
    """The success path must invoke 'exa-bundle init'."""

    def test_exasol_bundle_init_present(self):
        source = read_source()
        assert "exa-bundle init" in source, (
            "Expected 'exa-bundle init' in wrapper.js success path"
        )
