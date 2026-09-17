import pytest

from rechna import registry


@pytest.fixture(autouse=True)
def _isolated_registry():
    saved = registry._groups
    registry._groups = []
    try:
        yield
    finally:
        registry._groups = saved


def test_group_registers_function():
    @registry.group
    def a():
        yield "a", "Host a\n"

    assert registry.all_groups() == [a]
    assert registry.all_machines() == [("a", "Host a\n")]


def test_exact_duplicate_is_deduplicated():
    @registry.group
    def a():
        yield "shared", "Host shared\n"
        yield "a", "Host a\n"

    @registry.group
    def b():
        yield "shared", "Host shared\n"
        yield "b", "Host b\n"

    machines = registry.all_machines()
    assert machines == [
        ("shared", "Host shared\n"),
        ("a", "Host a\n"),
        ("b", "Host b\n"),
    ]


def test_conflicting_duplicate_raises():
    @registry.group
    def a():
        yield "x", "Host x\n    HostName one\n"

    @registry.group
    def b():
        yield "x", "Host x\n    HostName two\n"

    with pytest.raises(ValueError):
        registry.all_machines()
