import sys
import subprocess
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    """Post-installation hook to download the Go binary."""
    def run(self):
        # 1. Run standard pip installation for Python dependencies
        install.run(self)
        
        # 2. Execute the standalone _install.py script
        print("\n--- Running Exasol Post-Install Hook ---")
        try:
            subprocess.check_call([sys.executable, "-m", "exasol_bundle._install"])
        except subprocess.CalledProcessError as e:
            print(f"\n[WARNING] Auto-download of exasol-personal failed (Code {e.returncode}).")
            print("Please run manually: `exasol-bundle install-db`")

setup(
    name="exasol-bundle",  # ADD THIS: Forces sdist to recognize the package
    version="1.0.0",       # ADD THIS: Must match pyproject.toml
    cmdclass={
        'install': PostInstallCommand,
    },
)