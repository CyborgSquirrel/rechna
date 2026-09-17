import argparse
import os
import sys
import tempfile
from pathlib import Path

from . import machines  # noqa: F401 -- import triggers @group registration
from .registry import Machine, all_machines, filter_by_tags


def _write_ssh_config(machine: Machine) -> Path:
    """Write a single machine's (self-sufficient) config to a temp file."""
    path = Path(tempfile.gettempdir()) / f"rechna-{os.getuid()}.ssh_config"
    path.write_text(machine.config)
    return path


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

    connect_parser = sub.add_parser("connect", help="ssh into a machine by name")
    connect_parser.add_argument("name", help="machine name, as shown by `rechna list`")
    connect_parser.add_argument(
        "ssh_args",
        nargs=argparse.REMAINDER,
        help="extra arguments passed through to ssh",
    )

    args = parser.parse_args(argv)

    entries = all_machines()

    if args.command == "list":
        for name in filter_by_tags(entries, args.tag):
            print(name)
    elif args.command == "config":
        for machine in filter_by_tags(entries, args.tag).values():
            print(machine.config)
    elif args.command == "connect":
        if args.name not in entries:
            print(
                f"rechna: no such machine {args.name!r} (see `rechna list`)",
                file=sys.stderr,
            )
            raise SystemExit(1)
        config_path = _write_ssh_config(entries[args.name])
        os.execvp("ssh", ["ssh", "-F", str(config_path), args.name, *args.ssh_args])


if __name__ == "__main__":
    main()
