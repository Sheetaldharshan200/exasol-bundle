from exasol_bundle.core import ExasolComponent


class JsonTablesComponent(ExasolComponent):
    @property
    def name(self) -> str:
        return "json-tables"

    def install(self) -> None:
        print("\n=== Initializing Exasol JSON Tables ===")
        try:
            import exasol_json_tables  # noqa: F401
            print("✓ Exasol JSON Tables is already installed.")
        except ImportError:
            print("[ERROR] exasol-json-tables is not installed. Run: pip install exasol-bundle")
