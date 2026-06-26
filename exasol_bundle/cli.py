import argparse
import sys
from exasol_bundle import registry

def main():
    parser = argparse.ArgumentParser(description="Exasol Universal Bundler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize and configure all components")

    install_parser = subparsers.add_parser("install", help="Run the installation hook for a specific component")
    install_parser.add_argument("component", choices=[c.name for c in registry.get_all()])

    start_parser = subparsers.add_parser("start", help="Start a specific component")
    start_parser.add_argument("component", choices=[c.name for c in registry.get_all()])

    args = parser.parse_args()

    if args.command == "init":
        print("Starting universal initialization...")
        for comp in registry.get_all():
            comp.install()
        print("\nAll components initialized successfully!")

    elif args.command == "install":
        comp = registry.get_by_name(args.component)
        if comp:
            comp.install()
        else:
            print(f"Error: Component '{args.component}' not found in registry.")
            sys.exit(1)

    elif args.command == "start":
        comp = registry.get_by_name(args.component)
        if comp:
            comp.start()
        else:
            print(f"Error: Component '{args.component}' not found in registry.")
            sys.exit(1)

if __name__ == "__main__":
    main()