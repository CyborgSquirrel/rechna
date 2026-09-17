import argparse

from . import machines  # noqa: F401 -- import triggers @group registration
from .registry import all_machines, filter_by_tags


def _add_tag_filter(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--tag",
        action="append",
        help="only include machines with this tag (repeatable, OR'd together)",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rechna")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="print all expanded machine names")
    _add_tag_filter(list_parser)

    config_parser = sub.add_parser(
        "config", help="print full ssh_config text for all machines"
    )
    _add_tag_filter(config_parser)

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
