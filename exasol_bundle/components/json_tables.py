from exa_bundle.core import ExasolComponent

class JsonTablesComponent(ExasolComponent):
    @property
    def name(self) -> str:
        return "json-tables"

    def install(self) -> None:
        print("\n=== Initializing Exasol JSON Tables ===")
        try:
            import exasol_json_tables
            print(f"✓ Rust-backed JSON Tables extension installed and ready.")
        except ImportError:
            print("[ERROR] exasol-json-tables not found.")
            print("        Ensure pre-compiled wheels exist for your OS on PyPI.")