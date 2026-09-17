from rechna import machines
from rechna.registry import all_machines, filter_by_tags


def test_total_machine_count_and_uniqueness():
    entries = all_machines()
    assert len(entries) == 26  # tum-halle + 15 nc-9-* + 10 nc-11-*


def test_tum_halle_present_once_with_no_tags():
    entries = all_machines()
    assert "tum-halle" in entries
    tum_halle = entries["tum-halle"]
    assert "HostName halle.cit.tum.de" in tum_halle.config
    assert tum_halle.tags == frozenset()


def test_range_values_correlated_correctly():
    entries = all_machines()
    machine = entries["nc-9-3-2"]
    assert "Host nc-9-3-2" in machine.config
    assert "HostName nc-9-3-2.kosmos.cit.tum.de" in machine.config


def test_tags_by_machine_family():
    entries = all_machines()
    assert entries["nc-9-1-1"].tags == frozenset({"5090"})
    assert entries["nc-11-1-1"].tags == frozenset({"5080"})


def test_filter_by_tag_selects_only_matching_family_plus_shared():
    entries = all_machines()
    fifty_nineties = filter_by_tags(entries, ["5090"])
    assert set(fifty_nineties) == {f"nc-9-{a}-{b}" for a in range(1, 6) for b in range(1, 4)}


def test_each_group_is_independently_usable():
    for group_func in (machines.nc_9_5090, machines.nc_11_5080):
        entries = {name: (config, tags) for name, config, tags in group_func()}
        assert "tum-halle" in entries
        assert any(
            "ProxyJump tum-halle" in config
            for name, (config, tags) in entries.items()
            if name != "tum-halle"
        )


def test_each_machine_config_is_individually_self_sufficient():
    entries = all_machines()
    for name, machine in entries.items():
        if name == "tum-halle":
            continue
        assert "Host tum-halle" in machine.config
        assert f"Host {name}" in machine.config
