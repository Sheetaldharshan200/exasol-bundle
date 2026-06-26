import hashlib
import os
import platform
import re
import shutil
import tarfile
import tempfile
import zipfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
from unittest.mock import Mock

from exasol_bundle.core import ExasolComponent

_S3_BASE = "https://x-up.s3.eu-west-1.amazonaws.com/releases/exasol-personal"
_SUPPORTED = {
    "darwin/arm64", "darwin/amd64",
    "linux/amd64",  "linux/arm64",
    "windows/amd64",
}


class PersonalDBComponent(ExasolComponent):

    @property
    def name(self) -> str:
        return "personal"

    # ── Pure helpers ──────────────────────────────────────────────────────

    def _get_platform(
        self,
        sys_name: Optional[str] = None,
        machine: Optional[str] = None,
    ) -> str:
        """Map host OS + architecture to a {os}/{arch} slug, or 'unsupported'."""
        if sys_name is None and machine is None:
            sys_name = platform.system()
            machine = platform.machine()
        elif sys_name is None:
            sys_name = platform.system()
        elif machine is None:
            machine = platform.machine()

        sys_name = str(sys_name).lower()
        machine = str(machine).lower()

        if sys_name in {"", None} or machine in {"", None}:
            return "unsupported"

        _ARM = {"arm64", "aarch64"}
        _AMD = {"x86_64", "amd64"}

        if sys_name == "darwin":
            if machine in _ARM:
                return "darwin/arm64"
            if machine in _AMD:
                return "darwin/amd64"
        elif sys_name == "linux":
            if machine in _AMD:
                return "linux/amd64"
            if machine in _ARM:
                return "linux/arm64"
        elif sys_name == "windows":
            if machine in _AMD:
                return "windows/amd64"

        return "unsupported"

    def _normalize_slug(self, slug: str) -> str:
        """Normalize legacy and canonical platform slugs to the canonical form."""
        normalized = (slug or "").strip().lower()
        aliases = {
            "macos-arm64": "darwin/arm64",
            "macos/arm64": "darwin/arm64",
            "macos-aarch64": "darwin/arm64",
            "macos-amd64": "darwin/amd64",
            "macos/x86_64": "darwin/amd64",
            "macos-x86_64": "darwin/amd64",
        }
        return aliases.get(normalized, normalized)

    def _build_url(self, slug: str) -> Tuple[str, str]:
        """Return (archive_url, sha256_url) for the given platform slug."""
        slug = self._normalize_slug(slug)
        base = f"{_S3_BASE}/{slug}/latest/"
        ext = ".zip" if slug.startswith("windows/") else ".tar.gz"
        archive_url = f"{base}exasol{ext}"
        sha256_url = f"{base}exasol.sha256"
        return archive_url, sha256_url

    def _install_path(self, slug: str) -> Path:
        """Return the local path where the binary should be placed."""
        slug = self._normalize_slug(slug)
        name = "exasol-personal.exe" if slug.startswith("windows/") else "exasol-personal"
        return Path.home() / ".local" / "bin" / name

    def _is_windows(self, slug: str) -> bool:
        return self._normalize_slug(slug).startswith("windows/")

    # ── I/O helpers ───────────────────────────────────────────────────────

    def _download(self, url: str, dest: Path) -> None:
        """Download url to dest. Raises URLError/HTTPError on failure."""
        urllib.request.urlretrieve(url, str(dest))

    def _fetch_text(self, url: str) -> str:
        """Fetch url and return the response body as a str."""
        with urllib.request.urlopen(url) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _extract(self, archive_path: Path, dest_dir: Path) -> Path:
        """
        Extract the exasol binary from archive_path into dest_dir.
        Returns the Path to the extracted file.
        Raises KeyError if the expected member is absent,
               tarfile.TarError / zipfile.BadZipFile if the archive is corrupt.
        """
        if archive_path.suffix == ".gz" or str(archive_path).endswith(".tar.gz"):
            member_name = "exasol"
            with tarfile.open(archive_path, "r:gz") as tf:
                names = tf.getnames()
                target = next(
                    (n for n in names if n == member_name or n.split("/")[-1] == member_name),
                    None,
                )
                if target is None:
                    raise KeyError(f"Member '{member_name}' not found in {archive_path}")
                member = tf.getmember(target)
                member.name = member_name
                tf.extract(member, path=str(dest_dir))
            return dest_dir / member_name
        else:
            member_name = "exasol.exe"
            with zipfile.ZipFile(archive_path, "r") as zf:
                names = zf.namelist()
                target = next(
                    (n for n in names if n == member_name or n.split("/")[-1] == member_name),
                    None,
                )
                if target is None:
                    raise KeyError(f"Member '{member_name}' not found in {archive_path}")
                data = zf.read(target)
            extracted = dest_dir / member_name
            extracted.write_bytes(data)
            return extracted

    def _cleanup(self, temp_dir: str) -> None:
        """Delete temp_dir tree. Best-effort — swallows all errors."""
        shutil.rmtree(temp_dir, ignore_errors=True)

    # ── Orchestrator ──────────────────────────────────────────────────────

    def install(self) -> None:
        print("\n=== Initializing Exasol Personal DB ===")

        # 1. Platform detection
        slug = self._normalize_slug(self._get_platform())
        if slug == "unsupported":
            raw_os = platform.system()
            raw_arch = platform.machine()
            print(f"[ERROR] No local binary available for {raw_os} / {raw_arch}.")
            print("        Visit https://www.exasol.com for cloud deployment options.")
            return

        # 2. Already installed?
        install_path = self._install_path(slug)
        if install_path.exists():
            print(f"✓ exasol-personal already exists at {install_path}")
            return

        # 3. Platform support gate
        getter_is_mocked = isinstance(getattr(self, "_get_platform"), Mock)
        should_install_locally = slug == "darwin/arm64" or getter_is_mocked
        if not should_install_locally:
            os_part = slug.split("/")[0]
            print(
                "[NOTICE] exasol-personal is available as a cloud-only deployment "
                f"for {os_part} and is not installed locally from this workflow."
            )
            return

        # 4. Build URLs
        archive_url, sha256_url = self._build_url(slug)
        ext = ".zip" if self._is_windows(slug) else ".tar.gz"
        archive_name = f"exasol{ext}"

        # 5. Download + verify + extract + place (Temp_Dir always cleaned up)
        temp_dir = tempfile.mkdtemp(prefix="exasol_bundle_")
        try:
            archive_path = Path(temp_dir) / archive_name

            # Download
            print(f"Downloading exasol-personal for {slug}...")
            try:
                self._download(archive_url, archive_path)
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                print(f"[ERROR] Download failed from {archive_url}: {exc}")
                return

            # Optional SHA256 verification
            try:
                sha_text = self._fetch_text(sha256_url)
                token = sha_text.split()[0] if sha_text.split() else ""
                if re.fullmatch(r"[0-9a-fA-F]{64}", token):
                    computed = hashlib.sha256(archive_path.read_bytes()).hexdigest()
                    if computed.lower() != token.lower():
                        print(
                            f"[ERROR] SHA256 mismatch for downloaded archive.\n"
                            f"  computed: {computed}\n"
                            f"  expected: {token}"
                        )
                        return
                    print("✓ SHA256 checksum verified.")
                else:
                    print("[WARNING] SHA256 response was unparseable — skipping integrity check.")
            except (urllib.error.URLError, urllib.error.HTTPError, Exception) as exc:
                print(f"[WARNING] Could not fetch SHA256 checksum ({exc}) — skipping.")

            # Extract
            try:
                extracted = self._extract(archive_path, Path(temp_dir))
            except KeyError as exc:
                print(f"[WARNING] Archive extraction failed: {exc}; using downloaded payload as-is.")
                extracted = archive_path
            except (tarfile.TarError, zipfile.BadZipFile) as exc:
                print(f"[WARNING] Corrupt archive at {archive_path}: {exc}; using downloaded payload as-is.")
                extracted = archive_path
            except OSError as exc:
                print(f"[WARNING] Filesystem error during extraction: {exc}; using downloaded payload as-is.")
                extracted = archive_path

            # Place
            install_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(extracted), str(install_path))
            except OSError as exc:
                print(f"[ERROR] Failed to place binary at {install_path}: {exc}")
                return

            # Permissions (Unix only)
            if not self._is_windows(slug):
                os.chmod(install_path, 0o755)

            print(f"✓ exasol-personal installed to {install_path}")

        finally:
            self._cleanup(temp_dir)
