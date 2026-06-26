"""
Source-analysis unit tests for install.sh bootstrap_python() consent flow.

These tests read install.sh and assert structural properties about consent
prompts preceding every Linux sudo block, and the absence of prompts/sudo
in the macOS path.
"""

import re
from pathlib import Path

INSTALL_SH = (Path(__file__).parent.parent / "install.sh").read_text(encoding="utf-8")


def _block_between(content: str, start_marker: str, end_marker: str) -> str:
    """Extract content between start_marker and the next occurrence of end_marker."""
    start = content.find(start_marker)
    if start == -1:
        return ""
    end = content.find(end_marker, start + len(start_marker))
    if end == -1:
        return content[start:]
    return content[start:end]


def _prompt_precedes_sudo(content: str, sudo_cmd: str) -> bool:
    """Return True if [y/N] and read -r -p both appear before the *actual*
    sudo invocation (i.e. sudo_cmd at the start of a line, not inside an echo)."""
    # Find sudo_cmd that starts a line (actual invocation, not inside an echo string)
    match = re.search(r'^\s+' + re.escape(sudo_cmd), content, re.MULTILINE)
    if match is None:
        return False
    sudo_pos = match.start()
    before = content[:sudo_pos]
    return "[y/N]" in before and bool(re.search(r'\bread\b.*-p', before))


# ---------------------------------------------------------------------------
# 1–4: Each Linux package-manager block has a consent prompt before sudo
# ---------------------------------------------------------------------------

class TestAptHasConsentPrompt:
    """APT block must have [y/N] prompt and read -r -p before sudo apt-get."""

    def test_apt_has_yn_prompt(self):
        assert "[y/N]" in _block_between(INSTALL_SH, "apt-get &> /dev/null", "elif command -v dnf"), (
            "APT block must contain a [y/N] prompt"
        )

    def test_apt_has_read_prompt(self):
        apt_block = _block_between(INSTALL_SH, "apt-get &> /dev/null", "elif command -v dnf")
        assert re.search(r'\bread\b.*-p', apt_block), (
            "APT block must contain a 'read -r -p' consent prompt"
        )

    def test_prompt_precedes_sudo_apt(self):
        assert _prompt_precedes_sudo(INSTALL_SH, "sudo apt-get"), (
            "[y/N] prompt and read -r -p must appear before 'sudo apt-get'"
        )


class TestDnfHasConsentPrompt:
    """DNF block must have [y/N] prompt and read -r -p before sudo dnf."""

    def test_dnf_has_yn_prompt(self):
        dnf_block = _block_between(INSTALL_SH, "dnf &> /dev/null", "elif command -v pacman")
        assert "[y/N]" in dnf_block, "DNF block must contain a [y/N] prompt"

    def test_dnf_has_read_prompt(self):
        dnf_block = _block_between(INSTALL_SH, "dnf &> /dev/null", "elif command -v pacman")
        assert re.search(r'\bread\b.*-p', dnf_block), (
            "DNF block must contain a 'read -r -p' consent prompt"
        )

    def test_prompt_precedes_sudo_dnf(self):
        assert _prompt_precedes_sudo(INSTALL_SH, "sudo dnf"), (
            "[y/N] prompt and read -r -p must appear before 'sudo dnf'"
        )


class TestPacmanHasConsentPrompt:
    """Pacman block must have [y/N] prompt and read -r -p before sudo pacman."""

    def test_pacman_has_yn_prompt(self):
        pacman_block = _block_between(INSTALL_SH, "pacman &> /dev/null", "elif command -v zypper")
        assert "[y/N]" in pacman_block, "Pacman block must contain a [y/N] prompt"

    def test_pacman_has_read_prompt(self):
        pacman_block = _block_between(INSTALL_SH, "pacman &> /dev/null", "elif command -v zypper")
        assert re.search(r'\bread\b.*-p', pacman_block), (
            "Pacman block must contain a 'read -r -p' consent prompt"
        )

    def test_prompt_precedes_sudo_pacman(self):
        assert _prompt_precedes_sudo(INSTALL_SH, "sudo pacman"), (
            "[y/N] prompt and read -r -p must appear before 'sudo pacman'"
        )


class TestZypperHasConsentPrompt:
    """Zypper block must have [y/N] prompt and read -r -p before sudo zypper."""

    def test_zypper_has_yn_prompt(self):
        zypper_block = _block_between(INSTALL_SH, "zypper &> /dev/null", "else")
        assert "[y/N]" in zypper_block, "Zypper block must contain a [y/N] prompt"

    def test_zypper_has_read_prompt(self):
        zypper_block = _block_between(INSTALL_SH, "zypper &> /dev/null", "else")
        assert re.search(r'\bread\b.*-p', zypper_block), (
            "Zypper block must contain a 'read -r -p' consent prompt"
        )

    def test_prompt_precedes_sudo_zypper(self):
        assert _prompt_precedes_sudo(INSTALL_SH, "sudo zypper"), (
            "[y/N] prompt and read -r -p must appear before 'sudo zypper'"
        )


# ---------------------------------------------------------------------------
# 5: macOS path has no consent prompt and no sudo
# ---------------------------------------------------------------------------

class TestMacOsPathNoPropmt:
    """The darwin/Homebrew branch must NOT contain sudo or [y/N] prompts."""

    def _darwin_body(self) -> str:
        # Extract everything inside the darwin branch up to the first elif
        return _block_between(INSTALL_SH, '"darwin"*', "elif command -v apt-get")

    def test_darwin_branch_has_no_sudo(self):
        body = self._darwin_body()
        assert "sudo" not in body, (
            f"darwin branch must NOT call sudo.\nBranch content: {body!r}"
        )

    def test_darwin_branch_has_no_yn_prompt(self):
        body = self._darwin_body()
        assert "[y/N]" not in body, (
            "darwin branch must NOT contain a [y/N] consent prompt"
        )

    def test_darwin_branch_uses_brew(self):
        body = self._darwin_body()
        assert "brew install python" in body, (
            "darwin branch must call 'brew install python'"
        )


# ---------------------------------------------------------------------------
# 6: Python-already-present guard
# ---------------------------------------------------------------------------

class TestPythonAlreadyPresentGuard:
    """bootstrap_python() must be called inside `if ! command -v python3`."""

    def test_guard_condition_present(self):
        assert re.search(r'if\s*!\s*command\s+-v\s+python3', INSTALL_SH), (
            "Expected `if ! command -v python3` guard in install.sh"
        )

    def test_bootstrap_called_inside_guard(self):
        guard_match = re.search(
            r'if\s*!\s*command\s+-v\s+python3[^;]*?;\s*then(.*?)fi',
            INSTALL_SH,
            re.DOTALL,
        )
        assert guard_match is not None, (
            "Could not find the full `if ! command -v python3 ... fi` block"
        )
        assert "bootstrap_python" in guard_match.group(1), (
            "bootstrap_python() must be called inside the python3 absence guard"
        )
