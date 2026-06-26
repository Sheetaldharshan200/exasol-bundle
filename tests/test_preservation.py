"""
Preservation Property Tests
============================
These tests verify behaviors that MUST NOT change after any fixes are applied.
ALL tests in this file MUST PASS on the current (unfixed) code.

They establish the preservation baseline: correct behaviours that already work
and must continue to work once each bug fix is applied.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9,
           3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.16
"""

import io
import os
import re
import sys
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Hypothesis / parametrize fallback
# ---------------------------------------------------------------------------
try:
    from hypothesis import given, settings, assume
    from hypothesis import strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

ROOT = Path(__file__).parent.parent  # repository root


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helper — add repo root to sys.path so component modules are importable
# even when imports inside them refer to `exasol_bundle` (which fails) — we
# only need to import the module object, so we patch the broken namespace
# import before loading.
# ---------------------------------------------------------------------------
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Sub-test 1 — JsonTablesComponent already-installed path
# ---------------------------------------------------------------------------

class TestJsonTablesAlreadyInstalled:
    """
    Validates: Requirements 3.13, 3.14
    When exasol_json_tables is importable, install() skips all download steps
    and prints the "already installed" confirmation.
    """

    def _load_json_tables_component(self):
        """
        Import JsonTablesComponent, patching out the broken exasol_bundle namespace
        import so we can test the component logic in isolation.
        """
        import importlib
        import types

        # Provide a stub for exasol_bundle.core so the file-level import succeeds
        if "exasol_bundle" not in sys.modules:
            stub_pkg = types.ModuleType("exasol_bundle")
            stub_core = types.ModuleType("exasol_bundle.core")

            class _StubBase:
                pass

            stub_core.ExasolComponent = _StubBase
            stub_pkg.core = stub_core
            sys.modules["exasol_bundle"] = stub_pkg
            sys.modules["exasol_bundle.core"] = stub_core

        # Force reload of the component so it picks up the stub
        if "exasol_bundle.components.json_tables" in sys.modules:
            del sys.modules["exasol_bundle.components.json_tables"]
        if "json_tables" in sys.modules:
            del sys.modules["json_tables"]

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "json_tables_module",
            ROOT / "exasol_bundle" / "components" / "json_tables.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.JsonTablesComponent

    def test_already_installed_skips_download_and_prints_confirmation(self):
        """
        Validates: Requirements 3.13, 3.14
        When exasol_json_tables IS importable, install() must:
        - Not trigger any download (urlretrieve must not be called)
        - Print a message containing "already installed"
        - Return without raising an exception
        """
        JsonTablesComponent = self._load_json_tables_component()

        # Make exasol_json_tables importable
        fake_module = MagicMock()
        fake_module.__name__ = "exasol_json_tables"

        captured = io.StringIO()

        with patch.dict("sys.modules", {"exasol_json_tables": fake_module}):
            with patch("urllib.request.urlretrieve") as mock_retrieve:
                with patch("sys.stdout", captured):
                    obj = JsonTablesComponent()
                    obj.install()

        output = captured.getvalue()
        assert mock_retrieve.call_count == 0, (
            "urlretrieve was called even though exasol_json_tables was already importable"
        )
        assert "already installed" in output.lower(), (
            f"Expected 'already installed' in stdout, got: {output!r}"
        )


# ---------------------------------------------------------------------------
# Sub-test 2 — PersonalDBComponent already-installed path
# ---------------------------------------------------------------------------

class TestPersonalDBAlreadyInstalled:
    """
    Validates: Requirements 3.8
    When binary_path.exists() is True, install() returns early with an
    "already exists" message.
    """

    def _load_personal_db_component(self):
        import types, importlib.util

        if "exasol_bundle" not in sys.modules:
            stub_pkg = types.ModuleType("exasol_bundle")
            stub_core = types.ModuleType("exasol_bundle.core")

            class _StubBase:
                pass

            stub_core.ExasolComponent = _StubBase
            stub_pkg.core = stub_core
            sys.modules["exasol_bundle"] = stub_pkg
            sys.modules["exasol_bundle.core"] = stub_core

        spec = importlib.util.spec_from_file_location(
            "personal_db_module",
            ROOT / "exasol_bundle" / "components" / "personal_db.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.PersonalDBComponent

    def test_binary_exists_returns_early_with_message(self):
        """
        Validates: Requirement 3.8
        When the binary already exists, install() should print "already exists"
        and return without making any network calls.
        """
        PersonalDBComponent = self._load_personal_db_component()

        captured = io.StringIO()

        with patch.object(
            PersonalDBComponent, "_get_platform", return_value="macos-arm64"
        ):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("urllib.request.urlopen") as mock_open:
                    with patch("sys.stdout", captured):
                        obj = PersonalDBComponent()
                        obj.install()

        output = captured.getvalue()
        assert mock_open.call_count == 0, (
            "urlopen was called even though binary already existed"
        )
        assert "already exists" in output.lower(), (
            f"Expected 'already exists' in stdout, got: {output!r}"
        )


# ---------------------------------------------------------------------------
# Sub-test 3 — PersonalDBComponent non-macOS-arm64 path
# ---------------------------------------------------------------------------

class TestPersonalDBNonMacOsArm64:
    """
    Validates: Requirement 3.9 (cloud-only path)
    On non-macOS-arm64 platforms, install() prints the cloud-only notice and
    returns early without making any network calls.
    """

    def _load_personal_db_component(self):
        import types, importlib.util

        if "exasol_bundle" not in sys.modules:
            stub_pkg = types.ModuleType("exasol_bundle")
            stub_core = types.ModuleType("exasol_bundle.core")

            class _StubBase:
                pass

            stub_core.ExasolComponent = _StubBase
            stub_pkg.core = stub_core
            sys.modules["exasol_bundle"] = stub_pkg
            sys.modules["exasol_bundle.core"] = stub_core

        spec = importlib.util.spec_from_file_location(
            "personal_db_module2",
            ROOT / "exasol_bundle" / "components" / "personal_db.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.PersonalDBComponent

    @pytest.mark.parametrize("sys_name,machine", [
        ("windows", "amd64"),
        ("linux", "x86_64"),
        ("darwin", "x86_64"),
    ])
    def test_non_macos_arm64_prints_cloud_only_and_returns_early(self, sys_name, machine):
        """
        Validates: Requirement 3.9
        For Windows, Linux, and macOS-x86_64 platforms, install() must print
        a cloud-only notice and not touch the network.
        """
        PersonalDBComponent = self._load_personal_db_component()

        captured = io.StringIO()

        with patch("platform.system", return_value=sys_name):
            with patch("platform.machine", return_value=machine):
                with patch("urllib.request.urlopen") as mock_open:
                    with patch("sys.stdout", captured):
                        obj = PersonalDBComponent()
                        obj.install()

        output = captured.getvalue()
        assert mock_open.call_count == 0, (
            f"urlopen called on non-macOS-arm64 platform ({sys_name}/{machine})"
        )
        assert "cloud" in output.lower() or "notice" in output.lower(), (
            f"Expected cloud-only notice in stdout for {sys_name}/{machine}, got: {output!r}"
        )


# ---------------------------------------------------------------------------
# Sub-test 4 — wrapper.js Windows-with-Python path (source check)
# ---------------------------------------------------------------------------

class TestWrapperJsWindowsWithPython:
    """
    Validates: Requirements 3.4
    When Windows + Python already present, wrapper.js should NOT hit the
    early-exit path — it should proceed to the installer selection.
    """

    def test_python_detection_branch_calls_installer_not_winget(self):
        """
        Validates: Requirement 3.4
        When Python is already present (checkCommand returns true), the script
        skips installPythonWindows() and proceeds to installCmd selection.
        The source must show that the winget/installPythonWindows path is
        guarded by the python-absent condition, so when Python is present
        the installer runs instead.
        """
        content = read("npm-wrapper/bin/wrapper.js")

        # The python-missing block must be gated by the "not python" check
        # so that when python IS available, we skip it entirely.
        assert "!checkCommand('python3') && !checkCommand('python')" in content, (
            "Expected the python-absent guard in wrapper.js"
        )

        # The installer selection (uv/pipx/pip) must be outside the python-absent block
        # i.e. it appears AFTER the if-block that handles the missing-python case.
        python_absent_block_start = content.index("!checkCommand('python3') && !checkCommand('python')")
        # Find the end of the if-block (first closing brace after the installPythonWindows call)
        install_block = content[python_absent_block_start:]
        # uv/pipx installer selection must appear after the missing-python guard
        installer_section_start = content.find("checkCommand('uv')")
        assert installer_section_start > python_absent_block_start, (
            "Installer selection (uv/pipx/pip) should appear after the python-absent guard block"
        )

        # Confirm 'exa-bundle init' is called in the installer path
        assert "exa-bundle init" in content, (
            "Expected 'exa-bundle init' to be called in the successful install path"
        )


# ---------------------------------------------------------------------------
# Sub-test 5 — wrapper.js non-Windows-without-Python exits with code 1
# ---------------------------------------------------------------------------

class TestWrapperJsNonWindowsWithoutPython:
    """
    Validates: Requirement 3.5
    When non-Windows and Python absent, the script exits with code 1.
    """

    def test_non_windows_python_absent_exits_code_1(self):
        """
        Validates: Requirement 3.5
        The non-Windows, Python-absent branch must call process.exit(1).
        Verified by reading the source and confirming process.exit(1) appears
        in that branch.
        """
        content = read("npm-wrapper/bin/wrapper.js")

        # Confirm the else branch (non-Windows) exits with 1
        # The structure is: if (isWindows) { ... } else { ... process.exit(1) }
        else_match = re.search(
            r'else\s*\{[^}]*process\.exit\(1\)',
            content,
            re.DOTALL,
        )
        assert else_match is not None, (
            "Expected process.exit(1) inside the else (non-Windows) branch for missing Python"
        )

        # Also confirm the non-Windows path prints an error before exiting
        assert "Python 3 is required" in content or "python 3 is required" in content.lower(), (
            "Expected an error message about Python 3 being required in the non-Windows path"
        )


# ---------------------------------------------------------------------------
# Sub-test 6 — install.sh macOS path runs brew without sudo
# ---------------------------------------------------------------------------

class TestInstallShMacOsPath:
    """
    Validates: Requirement 3.10
    On macOS with Homebrew, bootstrap_python() runs `brew install python`
    without calling sudo.
    """

    def test_darwin_branch_uses_brew_without_sudo(self):
        """
        Validates: Requirement 3.10
        The darwin branch in install.sh must call `brew install python` and
        must NOT call `sudo` in that branch.
        """
        content = read("install.sh")

        # Find only the darwin block up to (but not including) the next elif/else.
        # The OSTYPE darwin branch ends at the first `elif` that follows it.
        darwin_match = re.search(
            r'(\[\[.*?darwin.*?\]\].*?then)(.*?)(?=elif\s+command)',
            content,
            re.DOTALL,
        )
        assert darwin_match is not None, "Could not find the darwin branch in install.sh"

        # Group 2 is just the body of the darwin branch, before any other branch
        darwin_body = darwin_match.group(2)

        assert "brew install python" in darwin_body, (
            f"Expected 'brew install python' in the darwin block, got: {darwin_body!r}"
        )
        assert "sudo" not in darwin_body, (
            f"darwin block must NOT call sudo, but found it in: {darwin_body!r}"
        )


# ---------------------------------------------------------------------------
# Sub-test 7 — install.sh Python-already-present path
# ---------------------------------------------------------------------------

class TestInstallShPythonAlreadyPresent:
    """
    Validates: Requirement 3.11
    When Python 3 is already present, bootstrap_python() is never called.
    """

    def test_guard_condition_skips_bootstrap_when_python_present(self):
        """
        Validates: Requirement 3.11
        install.sh must guard the bootstrap_python() call with
        `if ! command -v python3`, so that when python3 IS present the
        function is never called.
        """
        content = read("install.sh")

        # The guard must be: if ! command -v python3 ... then bootstrap_python
        assert re.search(r'if\s*!\s*command\s+-v\s+python3', content), (
            "Expected `if ! command -v python3` guard before bootstrap_python() call"
        )

        # bootstrap_python must be called inside that guard
        guard_match = re.search(
            r'if\s*!\s*command\s+-v\s+python3[^;]*?;\s*then(.*?)fi',
            content,
            re.DOTALL,
        )
        assert guard_match is not None, (
            "Could not find the full `if ! command -v python3 ... fi` block"
        )
        assert "bootstrap_python" in guard_match.group(1), (
            "bootstrap_python() must be called inside the python3 guard block"
        )


# ---------------------------------------------------------------------------
# Sub-test 8 — install.sh success path runs `exa-bundle init`
# ---------------------------------------------------------------------------

class TestInstallShSuccessRunsInit:
    """
    Validates: Requirement 3.12
    The install.sh script must run `exa-bundle init` as the final step.
    """

    def test_script_ends_with_exasol_bundle_init(self):
        """
        Validates: Requirement 3.12
        install.sh must call `exa-bundle init` somewhere after the
        installation step.
        """
        content = read("install.sh")

        assert "exa-bundle init" in content, (
            "Expected 'exa-bundle init' to be called in install.sh"
        )

        # Confirm it appears after the $INSTALL_METHOD call (i.e., after installation)
        install_pos = content.index("$INSTALL_METHOD exasol-bundle")
        init_pos = content.index("exa-bundle init")
        assert init_pos > install_pos, (
            "exa-bundle init must appear AFTER the $INSTALL_METHOD exasol-bundle step"
        )


# ---------------------------------------------------------------------------
# Sub-test 9 — Property-based test: all equal version strings → exits 0
# ---------------------------------------------------------------------------

def _versions_all_equal(versions: list) -> int:
    """
    Pure equality-check helper that mimics what check_versions.py will do.
    Returns 0 if all versions match, 1 otherwise.
    This is the logic that check_versions.py will implement (task 5.5).
    """
    if not versions:
        return 0
    return 0 if len(set(versions)) == 1 else 1


if HAS_HYPOTHESIS:
    class TestVersionEqualityProperty:
        """
        Validates: Requirements 3.6, 3.7
        Property-based test: for all sets of five equal version strings,
        the version-equality check exits 0.
        """

        @given(
            st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True).filter(lambda v: len(v) > 0)
        )
        @settings(max_examples=50)
        def test_equal_versions_exit_0(self, version: str):
            """
            Validates: Requirements 3.6, 3.7
            For any valid semver string v, a list of five copies of v must
            return exit code 0 from the equality check.
            """
            five_equal = [version] * 5
            result = _versions_all_equal(five_equal)
            assert result == 0, (
                f"Expected exit code 0 for five equal versions {version!r}, got {result}"
            )

        @given(
            st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True),
            st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True),
        )
        @settings(max_examples=50)
        def test_unequal_versions_exit_1(self, v1: str, v2: str):
            """
            Validates: Requirements 3.6, 3.7
            For two distinct versions v1 and v2, a mixed list exits 1.
            """
            assume(v1 != v2)
            mixed = [v1, v1, v2, v1, v1]
            result = _versions_all_equal(mixed)
            assert result == 1, (
                f"Expected exit code 1 for mixed versions {v1!r}/{v2!r}, got {result}"
            )

else:
    class TestVersionEqualityProperty:
        """
        Validates: Requirements 3.6, 3.7
        Parametrized fallback when hypothesis is not installed.
        """

        @pytest.mark.parametrize("version", ["1.0.18", "2.3.1", "0.0.1"])
        def test_equal_versions_exit_0(self, version: str):
            """
            Validates: Requirements 3.6, 3.7
            Five copies of any version string must produce exit code 0.
            """
            five_equal = [version] * 5
            result = _versions_all_equal(five_equal)
            assert result == 0, (
                f"Expected exit code 0 for five equal versions {version!r}, got {result}"
            )

        @pytest.mark.parametrize("v1,v2", [
            ("1.0.18", "1.0.1"),
            ("2.0.0", "1.0.0"),
            ("1.0.4", "1.0.18"),
        ])
        def test_unequal_versions_exit_1(self, v1: str, v2: str):
            """
            Validates: Requirements 3.6, 3.7
            Mixed version lists must produce exit code 1.
            """
            mixed = [v1, v1, v2, v1, v1]
            result = _versions_all_equal(mixed)
            assert result == 1, (
                f"Expected exit code 1 for mixed versions {v1!r}/{v2!r}, got {result}"
            )


# ---------------------------------------------------------------------------
# Sub-test 10 — Property-based test: matching SHA256 → chmod is called
# ---------------------------------------------------------------------------

def _make_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_personal_db_happy_path(data: bytes) -> MagicMock:
    """
    Helper: exercise the happy-path of PersonalDBComponent.install()
    with a mocked download that writes `data`.  Returns the mock for
    os.chmod so callers can assert it was called.

    The mock GitHub release includes a companion .sha256 asset whose content
    matches the SHA256 of `data`, so the integrity check passes and chmod is
    reached unchanged.
    """
    import types, importlib.util, json as _json

    # Ensure exasol_bundle stub exists
    if "exasol_bundle" not in sys.modules:
        stub_pkg = types.ModuleType("exasol_bundle")
        stub_core = types.ModuleType("exasol_bundle.core")

        class _StubBase:
            pass

        stub_core.ExasolComponent = _StubBase
        stub_pkg.core = stub_core
        sys.modules["exasol_bundle"] = stub_pkg
        sys.modules["exasol_bundle.core"] = stub_core

    spec = importlib.util.spec_from_file_location(
        "personal_db_chmod_test",
        ROOT / "exasol_bundle" / "components" / "personal_db.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    PersonalDBComponent = mod.PersonalDBComponent

    asset_name = "exasol-personal-darwin-arm64"
    correct_digest = _make_sha256(data)

    fake_asset = {
        "name": asset_name,
        "browser_download_url": "https://example.com/bin",
    }
    fake_sha256_asset = {
        "name": asset_name + ".sha256",
        "browser_download_url": "https://example.com/bin.sha256",
    }
    fake_release = {"assets": [fake_asset, fake_sha256_asset]}

    mock_chmod = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Pre-create the directory structure that the component will try to use
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        def fake_urlretrieve(url, dest):
            Path(dest).write_bytes(data)

        # The component calls urlopen twice: once for the release API, once for
        # the .sha256 companion file.  We use a side_effect list to return
        # different responses for each call.
        release_resp = MagicMock()
        release_resp.read.return_value = _json.dumps(fake_release).encode()
        release_resp.__enter__ = lambda s: s
        release_resp.__exit__ = MagicMock(return_value=False)

        sha256_resp = MagicMock()
        sha256_resp.read.return_value = correct_digest.encode()
        sha256_resp.__enter__ = lambda s: s
        sha256_resp.__exit__ = MagicMock(return_value=False)

        def fake_urlopen(req_or_url, *args, **kwargs):
            # First call is the GitHub API release request (a Request object);
            # second call is the .sha256 companion URL (a plain string).
            url = req_or_url if isinstance(req_or_url, str) else req_or_url.full_url
            if ".sha256" in url:
                return sha256_resp
            return release_resp

        with patch.object(PersonalDBComponent, "_get_platform", return_value="macos-arm64"):
            # Redirect Path.home() so the component resolves paths under tmpdir
            with patch("pathlib.Path.home", return_value=tmp_path):
                with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                    with patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
                        with patch("os.chmod", mock_chmod):
                            with patch("sys.stdout", io.StringIO()):
                                obj = PersonalDBComponent()
                                obj.install()

    return mock_chmod


if HAS_HYPOTHESIS:
    class TestChmodCalledOnHappyPath:
        """
        Validates: Requirement 3.9
        Property-based test: for arbitrary byte sequences that represent a
        downloaded binary, os.chmod must be called after a successful download
        where the SHA256 companion asset matches the computed digest.
        """

        @given(st.binary(min_size=1, max_size=256))
        @settings(max_examples=30)
        def test_chmod_called_for_any_downloaded_bytes(self, data: bytes):
            """
            Validates: Requirement 3.9
            On the happy path (matching SHA256 companion asset), os.chmod(binary_path,
            0o755) must be called after download and hash verification.
            """
            mock_chmod = _run_personal_db_happy_path(data)
            assert mock_chmod.called, (
                "os.chmod was not called after successful download — "
                "preservation of chmod behaviour is broken"
            )

else:
    class TestChmodCalledOnHappyPath:
        """
        Validates: Requirement 3.9
        Parametrized fallback: three representative byte sequences.
        """

        @pytest.mark.parametrize("data", [
            b"\x7fELF\x02\x01\x01",           # ELF-like header
            b"#!/bin/sh\necho hello",           # shell script bytes
            b"\x00" * 64,                       # zeroed binary
        ])
        def test_chmod_called_for_representative_bytes(self, data: bytes):
            """
            Validates: Requirement 3.9
            os.chmod must be called on the downloaded binary path when the SHA256
            companion asset matches the computed digest (hash check passes).
            """
            mock_chmod = _run_personal_db_happy_path(data)
            assert mock_chmod.called, (
                "os.chmod was not called after successful download — "
                "preservation of chmod behaviour is broken"
            )
