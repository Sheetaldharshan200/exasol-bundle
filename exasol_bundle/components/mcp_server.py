import os
import sys
import json
import subprocess
from pathlib import Path
from exa_bundle.core import ExasolComponent

class MCPServerComponent(ExasolComponent):
    @property
    def name(self) -> str:
        return "mcp"

    def install(self) -> None:
        print("\n=== Initializing Exasol MCP Server ===")
        try:
            import exasol_mcp_server
            print(f"✓ Python MCP Server package is installed and ready.")
        except ImportError:
            print("[ERROR] exasol-mcp-server not found in current environment.")

    def start(self) -> None:
        secrets_path = Path.home() / ".exasol" / "personal" / "deployments" / "default" / "secrets.json"
        env_vars = os.environ.copy()
        
        print("\n=== Starting Exasol MCP Server ===")
        if secrets_path.exists():
            print(f"Loading local database credentials from: {secrets_path}")
            try:
                with open(secrets_path, "r") as f:
                    secrets = json.load(f)
                    env_vars["EXA_DSN"] = secrets.get("dsn", "localhost:8563")
                    env_vars["EXA_USER"] = secrets.get("username", "sys")
                    env_vars["EXA_PASSWORD"] = secrets.get("password", "")
            except Exception as e:
                print(f"[WARNING] Could not parse secrets: {e}")
        else:
            print("[NOTICE] No local deployment credentials found. Falling back to system env vars.")

        try:
            print("Server process initiating...\n")
            subprocess.run([sys.executable, "-m", "exasol_mcp_server"], env=env_vars)
        except KeyboardInterrupt:
            print("\nMCP Server shutting down safely.")
        except Exception as e:
            print(f"\n[ERROR] Failed to start MCP Server: {e}")