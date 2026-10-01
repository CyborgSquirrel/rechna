import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import machines  # noqa: F401 -- import triggers @group registration
from . import status
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

    status_parser = sub.add_parser(
        "status", help="show GPU/CPU/memory/login status for GPU machines"
    )
    status_parser.add_argument(
        "--tag",
        action="append",
        help="only include machines with this tag (repeatable, OR'd together)",
    )
    status_parser.add_argument(
        "names",
        nargs="*",
        help="only check these specific machines (by exact name, as shown by "
        "`rechna list`); if omitted, checks every tagged (GPU) machine",
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
    elif args.command == "status":
        if args.names:
            unknown = [n for n in args.names if n not in entries]
            if unknown:
                print(
                    f"rechna: no such machine(s): {', '.join(unknown)} "
                    "(see `rechna list`)",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            base = {n: entries[n] for n in args.names}
        else:
            base = {name: m for name, m in entries.items() if m.tags}
        target = filter_by_tags(base, args.tag)
        print(status.format_table(status.probe_all(target)))
    elif args.command == "connect":
        if args.name not in entries:
            print(
                f"rechna: no such machine {args.name!r} (see `rechna list`)",
                file=sys.stderr,
            )
            raise SystemExit(1)
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "ssh_config"
            config_path.write_text(entries[args.name].config)
            # SHELL leaking into ssh's environment (e.g. from a non-POSIX
            # shell) has been observed to cause issues -- unset it.
            env = os.environ.copy()
            env.pop("SHELL", None)
            result = subprocess.run(
                ["ssh", "-F", str(config_path), args.name, *args.ssh_args],
                env=env,
            )
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
