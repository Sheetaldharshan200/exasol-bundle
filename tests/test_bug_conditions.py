"""
Bug Condition Exploration Tests
================================
These tests MUST FAIL on unfixed code — failure confirms the bugs exist.
DO NOT fix source files to make these pass; the tests encode the BUG CONDITIONS.

Each test asserts that the current (broken) state IS the buggy state.
After fixes are applied the assertions invert and the tests will PASS.

Counterexamples documented per bug:

Bug 7: `from exasol_bundle.core import ExasolComponent` raises ModuleNotFoundError
        because the installed source dir is `exasol_bundle/` but pyproject.toml
        instructs setuptools to include `exasol_bundle*` (zero modules packaged).

Bug 6: pyproject.toml dependencies list does NOT contain `exasol-json-tables`.
        JsonTablesComponent still contains `_get_wheel_name` and urllib download logic.

Bug 3: Five version strings differ:
        pyproject.toml = "1.0.18"
        exasol_bundle/__init__.py = "1.0.4"
        npm-wrapper/package.json = "1.0.1"
        homebrew/Formula/exasol-bundle.rb = "1.0.16" (from tarball URL)
        arch-linux/PKGBUILD = "1.0.16"

Bug 1: homebrew/Formula/exasol-bundle.rb sha256 is the literal stub
        "REPLACE_WITH_ACTUAL_SHA256_HASH".
        arch-linux/PKGBUILD sha256sums is the literal stub
        "REPLACE_WITH_ACTUAL_SHA256_HASH".

Bug 4: exasol_bundle/components/personal_db.py downloads a binary and calls
        os.chmod immediately — no SHA256 digest computation or comparison present.

Bug 5: install.sh bootstrap_python() runs `sudo apt-get`, `sudo pacman`, etc.
        with no read/prompt asking user for [y/N] consent beforehand.

Bug 2: npm-wrapper/bin/wrapper.js calls `process.exit(0)` after the Windows
        Python winget install, silently succeeding instead of asking the user
        to restart the terminal and re-run.
"""

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent  # repository root


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Bug 7 — Module Import Inconsistency (exasol_bundle vs exasol_bundle)
# ---------------------------------------------------------------------------

class TestBug7NamespaceMismatch:
    """Validates: Requirements 1.15, 1.16, 1.17"""

    def test_import_exasol_bundle_raises_module_not_found_error(self):
        """
        Bug 7 condition: `from exasol_bundle.core import ExasolComponent` raises
        ModuleNotFoundError because no `exasol_bundle` package exists on disk — the
        real source directory is `exasol_bundle/`.

        Counterexample: attempting the import always fails on unfixed code.
        """
        result = subprocess.run(
            [sys.executable, "-c", "from exasol_bundle.core import ExasolComponent"],
            capture_output=True,
            text=True,
        )
        # BUG CONDITION: the import FAILS (non-zero exit) on unfixed code.
        # After fix the import must succeed (exit 0). This assertion encodes
        # the expected FIXED behaviour — it will FAIL on current broken code.
        assert result.returncode == 0, (
            f"Bug 7 confirmed: 'from exasol_bundle.core import ExasolComponent' raised "
            f"ModuleNotFoundError.\nstderr: {result.stderr.strip()}"
        )

    def test_pyproject_include_pattern_is_exasol_bundle(self):
        """
        Bug 7 condition: pyproject.toml uses include = ["exasol_bundle*"] which
        causes setuptools to package zero modules.

        Counterexample: include pattern is "exasol_bundle*" not "exasol_bundle*".
        """
        content = read("pyproject.toml")
        # BUG: the current value is "exasol_bundle*" — this assertion expects the
        # FIXED value "exasol_bundle*" and therefore FAILS on unfixed code.
        assert 'include = ["exasol_bundle*"]' in content, (
            "Bug 7 confirmed: pyproject.toml still uses include = [\"exasol_bundle*\"] "
            "(not \"exasol_bundle*\"). Setuptools will package zero modules."
        )

    def test_pyproject_entry_point_is_exasol_bundle(self):
        """
        Bug 7 condition: entry point is `exasol_bundle.cli:main` (non-existent namespace).

        Counterexample: entry point resolves to missing module at runtime.
        """
        content = read("pyproject.toml")
        # BUG: current value is `exasol_bundle.cli:main` — this fails on unfixed code.
        assert 'exa-bundle = "exasol_bundle.cli:main"' in content, (
            "Bug 7 confirmed: pyproject.toml entry point is still "
            '"exasol_bundle.cli:main" (should be "exasol_bundle.cli:main").'
        )


# ---------------------------------------------------------------------------
# Bug 6 — Over-engineered Manual Wheel Distribution
# ---------------------------------------------------------------------------

class TestBug6ManualWheelAntiPattern:
    """Validates: Requirements 1.13, 1.14"""

    def test_pyproject_dependencies_contains_exasol_json_tables(self):
        """
        Bug 6 condition: exasol-json-tables is absent from [project.dependencies].

        Counterexample: the comment in pyproject.toml reads
        '# REMOVED exasol-json-tables. We handle this manually now.'
        """
        content = read("pyproject.toml")
        # BUG: dependency is missing — assertion expects it present, so FAILS now.
        # When no '#' comment exists, find("#") returns -1; treat that as "no comment
        # to precede" which means the entry (if present) is a real dependency line.
        first_comment = content.find("#")
        entry_pos = content.find("exasol-json-tables")
        is_real_entry = entry_pos != -1 and (first_comment == -1 or entry_pos < first_comment)
        assert is_real_entry, (
            "Bug 6 confirmed: exasol-json-tables is NOT in [project.dependencies]. "
            "The comment '# REMOVED exasol-json-tables...' is present instead."
        )

    def test_json_tables_component_does_not_contain_get_wheel_name(self):
        """
        Bug 6 condition: JsonTablesComponent.install() contains _get_wheel_name
        and custom download logic that re-implements what pip already handles.

        Counterexample: _get_wheel_name method and urlretrieve call present.
        """
        content = read("exasol_bundle/components/json_tables.py")
        # BUG: custom method exists — assertion expects it absent, so FAILS now.
        assert "_get_wheel_name" not in content, (
            "Bug 6 confirmed: JsonTablesComponent still contains _get_wheel_name "
            "(over-engineered custom wheel download logic)."
        )

    def test_json_tables_component_does_not_contain_urlretrieve(self):
        """
        Bug 6 condition: JsonTablesComponent contains urllib download logic.
        """
        content = read("exasol_bundle/components/json_tables.py")
        # BUG: urlretrieve present — assertion expects it absent, so FAILS now.
        assert "urlretrieve" not in content, (
            "Bug 6 confirmed: JsonTablesComponent still calls urllib.request.urlretrieve "
            "(should use pip/PyPI dependency instead)."
        )


# ---------------------------------------------------------------------------
# Bug 3 — Version Desynchronization Across Five Files
# ---------------------------------------------------------------------------

class TestBug3VersionDesynchronization:
    """Validates: Requirements 1.5, 1.6"""

    def _read_versions(self):
        # pyproject.toml: version = "x.y.z"
        pyproject = read("pyproject.toml")
        m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        pyproject_ver = m.group(1) if m else None

        # exasol_bundle/__init__.py
        # When __init__.py uses importlib.metadata dynamic lookup the runtime
        # version resolves to whatever is in pyproject.toml.  Detect the dynamic
        # pattern first; only fall back to a literal regex when it is absent.
        init_py = read("exasol_bundle/__init__.py")
        uses_dynamic_lookup = (
            "importlib.metadata" in init_py
            and re.search(r'__version__\s*=\s*version\s*\(', init_py) is not None
        )
        if uses_dynamic_lookup:
            # Dynamic lookup — effective version equals the canonical one.
            init_ver = pyproject_ver
        else:
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_py)
            init_ver = m.group(1) if m else None

        # npm-wrapper/package.json: "version": "x.y.z"
        npm = read("npm-wrapper/package.json")
        m = re.search(r'"version"\s*:\s*"([^"]+)"', npm)
        npm_ver = m.group(1) if m else None

        # homebrew formula: tarball URL contains version
        rb = read("homebrew/Formula/exasol-bundle.rb")
        m = re.search(r'exasol-bundle-(\d+\.\d+\.\d+)\.tar\.gz', rb)
        brew_ver = m.group(1) if m else None

        # arch-linux/PKGBUILD: pkgver=x.y.z
        pkgbuild = read("arch-linux/PKGBUILD")
        m = re.search(r'^pkgver=(\S+)', pkgbuild, re.MULTILINE)
        pkgbuild_ver = m.group(1) if m else None

        return {
            "pyproject.toml": pyproject_ver,
            "exasol_bundle/__init__.py": init_ver,
            "npm-wrapper/package.json": npm_ver,
            "homebrew/Formula/exasol-bundle.rb": brew_ver,
            "arch-linux/PKGBUILD": pkgbuild_ver,
        }

    def test_all_five_version_strings_are_equal(self):
        """
        Bug 3 condition: five version-bearing files hold different version strings.

        Counterexample:
            pyproject.toml              = "1.0.18"
            exasol_bundle/__init__.py   = "1.0.4"
            npm-wrapper/package.json    = "1.0.1"
            homebrew formula            = "1.0.16"
            arch-linux/PKGBUILD         = "1.0.16"
        """
        versions = self._read_versions()
        values = list(versions.values())
        all_equal = len(set(values)) == 1
        # BUG: versions differ — assertion expects them equal, so FAILS now.
        assert all_equal, (
            f"Bug 3 confirmed: version strings are NOT all equal.\n"
            + "\n".join(f"  {f}: {v}" for f, v in versions.items())
        )


# ---------------------------------------------------------------------------
# Bug 1 — Hardcoded Placeholder SHA256 Hashes
# ---------------------------------------------------------------------------

class TestBug1PlaceholderSha256:
    """Validates: Requirements 1.2, 1.3"""

    STUB = "REPLACE_WITH_ACTUAL_SHA256_HASH"

    def test_homebrew_formula_sha256_is_not_placeholder(self):
        """
        Bug 1 condition: homebrew/Formula/exasol-bundle.rb contains
        sha256 "REPLACE_WITH_ACTUAL_SHA256_HASH" — Homebrew rejects it.

        Counterexample: sha256 field is the literal stub string.
        """
        content = read("homebrew/Formula/exasol-bundle.rb")
        # BUG: stub present — assertion expects it absent, so FAILS now.
        assert self.STUB not in content, (
            f"Bug 1 confirmed: homebrew formula sha256 is still the literal stub "
            f'"{self.STUB}".'
        )

    def test_pkgbuild_sha256sums_is_not_placeholder(self):
        """
        Bug 1 condition: arch-linux/PKGBUILD sha256sums contains
        'REPLACE_WITH_ACTUAL_SHA256_HASH' — makepkg rejects it.

        Counterexample: sha256sums is the literal stub string.
        """
        content = read("arch-linux/PKGBUILD")
        # BUG: stub present — assertion expects it absent, so FAILS now.
        assert self.STUB not in content, (
            f"Bug 1 confirmed: PKGBUILD sha256sums is still the literal stub "
            f'"{self.STUB}".'
        )


# ---------------------------------------------------------------------------
# Bug 4 — No SHA256 Validation for Downloaded Binaries
# ---------------------------------------------------------------------------

class TestBug4NoSha256Validation:
    """Validates: Requirements 1.7, 1.8"""

    def test_personal_db_install_contains_sha256_verification(self):
        """
        Bug 4 condition: PersonalDBComponent.install() downloads a binary via
        urlretrieve and immediately calls os.chmod with no SHA256 check.

        Counterexample: the source of personal_db.py contains neither
        'hashlib' nor any sha256 digest comparison.
        """
        content = read("exasol_bundle/components/personal_db.py")
        # BUG: hashlib absent — assertion expects it present, so FAILS now.
        assert "hashlib" in content, (
            "Bug 4 confirmed: exasol_bundle/components/personal_db.py does NOT "
            "import hashlib or perform any SHA256 verification after download."
        )

    def test_personal_db_install_computes_and_compares_digest(self):
        """
        Bug 4 condition: no digest comparison logic present at all.
        """
        content = read("exasol_bundle/components/personal_db.py")
        # BUG: sha256 comparison absent — assertion expects it present, FAILS now.
        assert "sha256" in content.lower(), (
            "Bug 4 confirmed: personal_db.py contains no SHA256 comparison logic — "
            "any tampered binary would be accepted silently."
        )


# ---------------------------------------------------------------------------
# Bug 5 — Silent sudo in install.sh Without User Consent
# ---------------------------------------------------------------------------

class TestBug5SilentSudo:
    """Validates: Requirements 1.9, 1.10, 1.11, 1.12"""

    def test_bootstrap_python_prompts_user_before_sudo(self):
        """
        Bug 5 condition: bootstrap_python() calls sudo apt-get / pacman / dnf /
        zypper without first presenting a [y/N] prompt to the user.

        Counterexample: searching install.sh for a read/prompt construct before
        each sudo block reveals none exists.
        """
        content = read("install.sh")
        # BUG: no [y/N] prompt present — assertion expects one, so FAILS now.
        has_prompt = bool(re.search(r'\[y/N\]', content, re.IGNORECASE))
        assert has_prompt, (
            "Bug 5 confirmed: install.sh bootstrap_python() contains no [y/N] "
            "consent prompt before running sudo commands."
        )

    def test_bootstrap_python_uses_read_for_consent(self):
        """
        Bug 5 condition: the shell function never calls `read` to capture user input.
        """
        content = read("install.sh")
        # BUG: no `read -r -p` call in the sudo blocks — FAILS now.
        has_read_prompt = bool(re.search(r'\bread\b.*-p', content))
        assert has_read_prompt, (
            "Bug 5 confirmed: bootstrap_python() has no `read -r -p` call to "
            "capture user consent before executing sudo."
        )


# ---------------------------------------------------------------------------
# Bug 2 — Broken Windows Installation in NPM Wrapper
# ---------------------------------------------------------------------------

class TestBug2WindowsEarlyExit:
    """Validates: Requirements 1.4"""

    def test_wrapper_js_exits_with_nonzero_after_windows_python_install(self):
        """
        Bug 2 condition: wrapper.js calls process.exit(0) after installing Python
        via winget on Windows, causing npm to report success while exasol-bundle
        itself was never installed.

        Counterexample: the source contains `process.exit(0)` immediately after
        the installPythonWindows() call.
        """
        content = read("npm-wrapper/bin/wrapper.js")
        # BUG: process.exit(0) present — assertion expects it absent (fixed to
        # exit(1) with a restart message), so FAILS now.
        assert "process.exit(0)" not in content, (
            "Bug 2 confirmed: wrapper.js still calls process.exit(0) after the "
            "Windows Python install — the process silently succeeds before "
            "exasol-bundle is actually installed."
        )

    def test_wrapper_js_informs_user_to_restart_terminal(self):
        """
        Bug 2 condition: no restart-terminal message is present in the Windows
        post-install path.
        """
        content = read("npm-wrapper/bin/wrapper.js")
        # BUG: restart message absent — assertion expects it present, FAILS now.
        has_restart_message = (
            "restart" in content.lower() and "terminal" in content.lower()
            and "re-run" in content.lower()
        )
        assert has_restart_message, (
            "Bug 2 confirmed: wrapper.js does not tell the Windows user to restart "
            "their terminal and re-run the command after Python is installed."
        )
