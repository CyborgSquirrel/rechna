import argparse

from . import machines  # noqa: F401 -- import triggers @group registration
from .registry import all_machines, filter_by_tags


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rechna")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="print all expanded machine names")
    list_parser.add_argument(
        "--tag",
        action="append",
        help="only include machines with this tag (repeatable, OR'd together)",
    )

    config_parser = sub.add_parser(
        "config", help="print full ssh_config text for all machines"
    )
    config_parser.add_argument(
        "--tag",
        action="append",
        help="only include machines with this tag (repeatable, OR'd together)",
    )

    args = parser.parse_args(argv)

    entries = filter_by_tags(all_machines(), args.tag)
    if args.command == "list":
        for name in entries:
            print(name)
    elif args.command == "config":
        for machine in entries.values():
            print(machine.config)


if __name__ == "__main__":
    main()
