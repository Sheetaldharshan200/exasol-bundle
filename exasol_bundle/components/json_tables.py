import os
import sys
import platform
import subprocess
import urllib.request
from pathlib import Path
from exa_bundle.core import ExasolComponent

class JsonTablesComponent(ExasolComponent):
    @property
    def name(self) -> str:
        return "json-tables"

    def _get_wheel_name(self) -> str:
        """Determines the correct wheel filename based on the user's OS and CPU."""
        sys_name = platform.system().lower()
        machine = platform.machine().lower()

        # NOTE: You will need to update the version number "1.0.0" below 
        # to match whatever version of exasol-json-tables you built via Actions.
        base_name = "exasol_json_tables-1.0.0"

        if sys_name == "windows":
            return f"{base_name}-cp311-none-win_amd64.whl"
        elif sys_name == "darwin":
            if machine in ["arm64", "aarch64"]:
                return f"{base_name}-cp311-none-macosx_11_0_arm64.whl"
            else:
                return f"{base_name}-cp311-none-macosx_10_12_x86_64.whl"
        elif sys_name == "linux":
            if machine in ["aarch64", "arm64"]:
                return f"{base_name}-cp311-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"
            else:
                return f"{base_name}-cp311-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
        
        raise OSError(f"Unsupported platform for pre-compiled wheels: {sys_name} {machine}")

    def install(self) -> None:
        print("\n=== Initializing Exasol JSON Tables ===")
        
        try:
            import exasol_json_tables
            print("✓ Rust-backed JSON Tables extension is already installed.")
            return
        except ImportError:
            pass # We need to install it

        try:
            wheel_filename = self._get_wheel_name()
            # Replace YOUR_ORG/exa-bundle with your actual GitHub repository
            download_url = f"https://github.com/YOUR_ORG/exa-bundle/releases/download/upstream-dependencies/{wheel_filename}"
            
            download_dir = Path.home() / ".local" / "exa_bundle_cache"
            download_dir.mkdir(parents=True, exist_ok=True)
            wheel_path = download_dir / wheel_filename

            print(f"Downloading pre-compiled Rust wheel for your OS...")
            print(f"URL: {download_url}")
            
            urllib.request.urlretrieve(download_url, wheel_path)
            
            print("Installing wheel into the current environment...")
            # Run pip install safely via subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", str(wheel_path)])
            
            print("✓ Exasol JSON Tables successfully installed (Zero-Rust fallback).")
            
            # Clean up the downloaded file to save space
            os.remove(wheel_path)

        except Exception as e:
            print(f"[ERROR] Failed to install json-tables: {e}")