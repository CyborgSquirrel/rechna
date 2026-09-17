from rechna import machines
from rechna.registry import all_machines


def test_total_machine_count_and_uniqueness():
    entries = all_machines()
    names = [name for name, _ in entries]
    assert len(names) == len(set(names))
    assert len(names) == 26  # tum-halle + 15 nc-9-* + 10 nc-11-*


def test_tum_halle_present_once():
    entries = dict(all_machines())
    assert "tum-halle" in entries
    assert "HostName halle.cit.tum.de" in entries["tum-halle"]


def test_range_values_correlated_correctly():
    entries = dict(all_machines())
    text = entries["nc-9-3-2"]
    assert "Host nc-9-3-2" in text
    assert "HostName nc-9-3-2.kosmos.cit.tum.de" in text


def test_each_group_is_independently_usable():
    for group_func in (machines.nc_9_5090, machines.nc_11_5080):
        entries = dict(group_func())
        assert "tum-halle" in entries
        assert "ProxyJump tum-halle" in next(
            text for name, text in group_func() if name != "tum-halle"
        )
