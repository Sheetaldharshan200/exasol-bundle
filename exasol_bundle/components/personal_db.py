import os
import platform
import urllib.request
import json
from pathlib import Path
from exa_bundle.core import ExasolComponent

class PersonalDBComponent(ExasolComponent):
    @property
    def name(self) -> str:
        return "personal"

    def _get_platform(self) -> str:
        sys_name = platform.system().lower()
        machine = platform.machine().lower()
        
        if sys_name == "darwin" and machine in ["arm64", "aarch64"]:
            return "macos-arm64"
        return "cloud-only"

    def install(self) -> None:
        print("\n=== Initializing Exasol Personal DB ===")
        plat = self._get_platform()
        
        if plat == "cloud-only":
            print("[NOTICE] Local Exasol Personal deployment is macOS Apple Silicon exclusive.")
            print("         For Windows/Linux, the CLI expects AWS/Azure credentials.")
            return

        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        binary_path = bin_dir / "exasol-personal"

        if binary_path.exists():
            print(f"✓ Binary already exists at {binary_path}")
            return

        print("Fetching macOS Apple Silicon binary from GitHub Releases...")
        url = "https://api.github.com/repos/exasol/exasol-personal/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "exa-bundle", "Accept": "application/vnd.github.v3+json"})
        
        try:
            with urllib.request.urlopen(req) as res:
                release_data = json.loads(res.read().decode())
                assets = release_data.get("assets", [])
                
                for asset in assets:
                    if "darwin" in asset["name"] and "arm64" in asset["name"]:
                        target_url = asset["browser_download_url"]
                        print(f"Downloading: {asset['name']}")
                        urllib.request.urlretrieve(target_url, binary_path)
                        os.chmod(binary_path, 0o755)
                        print(f"✓ Successfully installed binary to {binary_path}")
                        return
            print("[ERROR] Could not find a matching darwin-arm64 release asset.")
        except Exception as e:
            print(f"[ERROR] Installation failed: {e}")