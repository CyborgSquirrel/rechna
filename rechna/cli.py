import argparse

from . import machines  # noqa: F401 -- import triggers @group registration
from .registry import all_machines


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rechna")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="print all expanded machine names")
    sub.add_parser("config", help="print full ssh_config text for all machines")
    args = parser.parse_args(argv)

    entries = all_machines()
    if args.command == "list":
        for name, _ in entries:
            print(name)
    elif args.command == "config":
        for _, text in entries:
            print(text)


if __name__ == "__main__":
    main()
