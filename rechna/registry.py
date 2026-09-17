"""Registry of host-group generator functions.

A "group" is a zero-argument generator function that yields
``(name, config_text)`` pairs, where ``config_text`` is a complete
``Host ...`` block suitable for an ssh_config file. Decorate a function
with ``@group`` to register it; the CLI collects every registered group
by import order.
"""

from collections.abc import Callable, Iterator

Group = Callable[[], Iterator[tuple[str, str]]]

_groups: list[Group] = []


def group(func: Group) -> Group:
    """Register ``func`` as a host group."""
    _groups.append(func)
    return func


def all_groups() -> list[Group]:
    return list(_groups)


def all_machines() -> list[tuple[str, str]]:
    """Run every registered group and flatten the results.

    Groups are allowed to independently re-yield the same machine (e.g. a
    shared jump host each group embeds so it can stand alone) as long as
    they agree on its config text; an exact duplicate is kept once. A name
    reused with different text is a genuine conflict and raises.
    """
    seen: dict[str, str] = {}
    machines: list[tuple[str, str]] = []
    for func in _groups:
        for name, text in func():
            if name in seen:
                if seen[name] != text:
                    raise ValueError(
                        f"machine {name!r} yielded with conflicting config "
                        f"text by multiple groups"
                    )
                continue
            seen[name] = text
            machines.append((name, text))
    return machines
