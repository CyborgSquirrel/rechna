"""Registry of host-group generator functions.

A "group" is a zero-argument generator function that yields
``(name, config_text, tags)`` triples, where ``config_text`` is a complete
``Host ...`` block suitable for an ssh_config file and ``tags`` is an
iterable of strings describing the machine (e.g. GPU model). Decorate a
function with ``@group`` to register it; the CLI collects every registered
group by import order.
"""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

Group = Callable[[], Iterator[tuple[str, str, Iterable[str]]]]

_groups: list[Group] = []


@dataclass(frozen=True)
class Machine:
    name: str
    config: str
    tags: frozenset[str] = frozenset()


def group(func: Group) -> Group:
    """Register ``func`` as a host group."""
    _groups.append(func)
    return func


def all_groups() -> list[Group]:
    return list(_groups)


def all_machines() -> dict[str, Machine]:
    """Run every registered group and merge the results into name -> Machine.

    Groups are allowed to independently re-yield the same machine (e.g. a
    shared jump host each group embeds so it can stand alone) as long as
    they agree on its config text and tags; an exact duplicate is kept
    once. A name reused with a different config or tags is a genuine
    conflict and raises.
    """
    machines: dict[str, Machine] = {}
    for func in _groups:
        for name, config, tags in func():
            machine = Machine(name=name, config=config, tags=frozenset(tags))
            existing = machines.get(name)
            if existing is not None:
                if existing != machine:
                    raise ValueError(
                        f"machine {name!r} yielded with conflicting "
                        f"definitions by multiple groups"
                    )
                continue
            machines[name] = machine
    return machines


def filter_by_tags(
    machines: dict[str, Machine], tags: Iterable[str] | None
) -> dict[str, Machine]:
    """Keep only machines that have at least one of ``tags``.

    ``tags`` of None or empty means no filtering.
    """
    if not tags:
        return dict(machines)
    wanted = set(tags)
    return {name: m for name, m in machines.items() if m.tags & wanted}
