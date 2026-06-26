#!/usr/bin/env python3
"""
CI guard script: verify that all static version files stay in sync with
the canonical version declared in pyproject.toml.

Files checked:
  - pyproject.toml           (canonical source of truth)
  - npm-wrapper/package.json
  - homebrew/Formula/exasol-bundle.rb
  - arch-linux/PKGBUILD

Usage (run from the repository root):
    python scripts/check_versions.py

Exit codes:
    0  all files report the same version
    1  one or more files differ from the canonical version
"""

import json
import re
import sys
from pathlib import Path

# Python ≥ 3.11 ships tomllib in the standard library; fall back to tomli for
# older interpreters (install with: pip install tomli).
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-reuse-local]
    except ImportError:
        print(
            "[ERROR] tomli is required on Python < 3.11.  "
            "Install it with: pip install tomli",
            file=sys.stderr,
        )
        sys.exit(2)


ROOT = Path(__file__).parent.parent


def read_pyproject_version() -> str:
    """Read the canonical version from pyproject.toml."""
    path = ROOT / "pyproject.toml"
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def read_npm_version() -> str:
    """Read version from npm-wrapper/package.json."""
    path = ROOT / "npm-wrapper" / "package.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data["version"]


def read_homebrew_version() -> str:
    """
    Extract version from the tarball URL in homebrew/Formula/exasol-bundle.rb.

    Expected line pattern:
        url "https://.../exasol-bundle-X.Y.Z.tar.gz"
    """
    path = ROOT / "homebrew" / "Formula" / "exasol-bundle.rb"
    content = path.read_text(encoding="utf-8")
    m = re.search(r'exasol-bundle-(\d+\.\d+\.\d+)\.tar\.gz', content)
    if not m:
        raise ValueError(
            f"Could not find a version string in {path} "
            "(expected pattern: exasol-bundle-X.Y.Z.tar.gz)"
        )
    return m.group(1)


def read_pkgbuild_version() -> str:
    """
    Extract pkgver from arch-linux/PKGBUILD.

    Expected line pattern:
        pkgver=X.Y.Z
    """
    path = ROOT / "arch-linux" / "PKGBUILD"
    content = path.read_text(encoding="utf-8")
    m = re.search(r'^pkgver=(\S+)', content, re.MULTILINE)
    if not m:
        raise ValueError(
            f"Could not find 'pkgver=...' in {path}"
        )
    return m.group(1)


def main() -> int:
    canonical = read_pyproject_version()

    sources = {
        "pyproject.toml": canonical,
        "npm-wrapper/package.json": read_npm_version(),
        "homebrew/Formula/exasol-bundle.rb": read_homebrew_version(),
        "arch-linux/PKGBUILD": read_pkgbuild_version(),
    }

    # ── Print the version table ──────────────────────────────────────────────
    col_file = max(len(f) for f in sources) + 2
    col_ver  = max(len(v) for v in sources.values()) + 2

    header = f"{'File':<{col_file}}  {'Version':<{col_ver}}  Status"
    print(header)
    print("-" * len(header))

    mismatches: list[tuple[str, str]] = []
    for file, ver in sources.items():
        if ver == canonical:
            status = "✓  OK"
        else:
            status = f"✗  MISMATCH (expected {canonical})"
            mismatches.append((file, ver))
        print(f"{file:<{col_file}}  {ver:<{col_ver}}  {status}")

    print()

    # ── Summary ──────────────────────────────────────────────────────────────
    if mismatches:
        print(f"[FAIL] {len(mismatches)} file(s) out of sync with the canonical version {canonical!r}:")
        for file, ver in mismatches:
            print(f"  {file}: {ver!r} != {canonical!r}")
        return 1

    print(f"[OK] All version files are in sync: {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
