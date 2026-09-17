from types import SimpleNamespace

from rechna import status
from rechna.registry import Machine


def _fake_completed(stdout: str, returncode: int = 0):
    return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)


def test_probe_machine_uses_batch_mode_and_accepts_new_host_keys(monkeypatch):
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        return _fake_completed("RECHNA_STATUS||0|0|-\n")

    monkeypatch.setattr("rechna.status.subprocess.run", fake_run)
    machine = Machine("nc-9-1-1", "Host nc-9-1-1\n", frozenset({"5090"}))

    status.probe_machine(machine)

    argv = captured["argv"]
    assert "BatchMode=yes" in argv
    # BatchMode disables prompts entirely, so a never-seen host key must
    # be auto-accepted (not left to hang/fail on a prompt that can't show).
    assert "StrictHostKeyChecking=accept-new" in argv


def test_probe_machine_parses_single_gpu(monkeypatch):
    monkeypatch.setattr(
        "rechna.status.subprocess.run",
        lambda *a, **k: _fake_completed(
            "Warning: motd noise\nRECHNA_STATUS|97, 23800, 24564;|42|55|jdoe\n"
        ),
    )
    machine = Machine("nc-9-1-1", "Host nc-9-1-1\n", frozenset({"5090"}))

    result = status.probe_machine(machine)

    assert result.name == "nc-9-1-1"
    assert result.error is None
    assert len(result.gpus) == 1
    util, mem_pct = result.gpus[0]
    assert util == 97
    assert round(mem_pct) == round(23800 / 24564 * 100)
    assert result.cpu_pct == 42
    assert result.mem_pct == 55
    assert result.users == ["jdoe"]


def test_probe_machine_parses_multiple_gpus(monkeypatch):
    monkeypatch.setattr(
        "rechna.status.subprocess.run",
        lambda *a, **k: _fake_completed(
            "RECHNA_STATUS|10, 100, 1000;20, 200, 2000;|5|10|-\n"
        ),
    )
    machine = Machine("multi-gpu", "Host multi-gpu\n", frozenset())

    result = status.probe_machine(machine)

    assert result.error is None
    assert len(result.gpus) == 2
    assert result.gpus[0] == (10.0, 10.0)
    assert result.gpus[1] == (20.0, 10.0)
    assert result.users == []


def test_probe_machine_no_gpu(monkeypatch):
    monkeypatch.setattr(
        "rechna.status.subprocess.run",
        lambda *a, **k: _fake_completed("RECHNA_STATUS||12|33|-\n"),
    )
    machine = Machine("tum-halle", "Host tum-halle\n", frozenset())

    result = status.probe_machine(machine)

    assert result.error is None
    assert result.gpus == []
    assert result.cpu_pct == 12
    assert result.mem_pct == 33


def test_probe_machine_missing_sentinel_is_unreachable(monkeypatch):
    monkeypatch.setattr(
        "rechna.status.subprocess.run",
        lambda *a, **k: _fake_completed("connection reset by peer\n", returncode=255),
    )
    machine = Machine("dead", "Host dead\n", frozenset())

    result = status.probe_machine(machine)

    assert result.error == "unreachable"


def test_probe_machine_timeout_is_unreachable(monkeypatch):
    import subprocess

    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="ssh", timeout=8)

    monkeypatch.setattr("rechna.status.subprocess.run", raise_timeout)
    machine = Machine("slow", "Host slow\n", frozenset())

    result = status.probe_machine(machine)

    assert result.error == "unreachable"


def test_probe_machine_malformed_line_is_bad_response(monkeypatch):
    monkeypatch.setattr(
        "rechna.status.subprocess.run",
        lambda *a, **k: _fake_completed("RECHNA_STATUS|not-enough-fields\n"),
    )
    machine = Machine("weird", "Host weird\n", frozenset())

    result = status.probe_machine(machine)

    assert result.error == "bad response"


def test_probe_all_preserves_name_order_and_mixed_results(monkeypatch):
    machines = {
        "b": Machine("b", "Host b\n", frozenset()),
        "a": Machine("a", "Host a\n", frozenset()),
        "c": Machine("c", "Host c\n", frozenset()),
    }

    def fake_probe(machine, timeout=8.0):
        if machine.name == "c":
            return status.MachineStatus("c", [], None, None, [], error="unreachable")
        return status.MachineStatus(machine.name, [], 0.0, 0.0, [])

    monkeypatch.setattr("rechna.status.probe_machine", fake_probe)

    results = status.probe_all(machines)

    assert [r.name for r in results] == ["a", "b", "c"]
    assert results[2].error == "unreachable"


def test_format_table_includes_headers_and_rows():
    statuses = [
        status.MachineStatus("nc-9-1-1", [(97.0, 96.9)], 42.0, 55.0, ["jdoe"]),
        status.MachineStatus("nc-9-1-2", [], 0.0, 5.0, []),
        status.MachineStatus("nc-9-1-3", [], None, None, [], error="unreachable"),
    ]

    table = status.format_table(statuses)

    assert "MACHINE" in table
    assert "GPU%" in table
    assert "GPU MEM%" in table
    assert "CPU%" in table
    assert "CPU MEM%" in table
    assert "USERS" in table
    assert "nc-9-1-1" in table
    assert "jdoe" in table
    assert "97%" in table
    assert "(unreachable)" in table
