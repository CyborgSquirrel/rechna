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
        yield "a", "Host a\n", ()

    assert registry.all_groups() == [a]
    assert registry.all_machines() == {
        "a": registry.Machine("a", "Host a\n", frozenset())
    }


def test_tags_are_stored_as_frozenset():
    @registry.group
    def a():
        yield "a", "Host a\n", ("5090", "5090")

    machines = registry.all_machines()
    assert machines["a"].tags == frozenset({"5090"})


def test_exact_duplicate_is_deduplicated():
    @registry.group
    def a():
        yield "shared", "Host shared\n", ()
        yield "a", "Host a\n", ("5090",)

    @registry.group
    def b():
        yield "shared", "Host shared\n", ()
        yield "b", "Host b\n", ("5080",)

    machines = registry.all_machines()
    assert set(machines) == {"shared", "a", "b"}
    assert machines["shared"].tags == frozenset()


def test_conflicting_duplicate_raises():
    @registry.group
    def a():
        yield "x", "Host x\n    HostName one\n", ()

    @registry.group
    def b():
        yield "x", "Host x\n    HostName two\n", ()

    with pytest.raises(ValueError):
        registry.all_machines()


def test_conflicting_tags_raises():
    @registry.group
    def a():
        yield "x", "Host x\n", ("5090",)

    @registry.group
    def b():
        yield "x", "Host x\n", ("5080",)

    with pytest.raises(ValueError):
        registry.all_machines()


def test_filter_by_tags():
    machines = {
        "a": registry.Machine("a", "Host a\n", frozenset({"5090"})),
        "b": registry.Machine("b", "Host b\n", frozenset({"5080"})),
        "c": registry.Machine("c", "Host c\n", frozenset()),
    }

    assert registry.filter_by_tags(machines, None) == machines
    assert registry.filter_by_tags(machines, []) == machines
    assert set(registry.filter_by_tags(machines, ["5090"])) == {"a"}
    assert set(registry.filter_by_tags(machines, ["5090", "5080"])) == {"a", "b"}
    assert set(registry.filter_by_tags(machines, ["nonexistent"])) == set()
