from pathlib import Path
from types import SimpleNamespace

import pytest

from rechna.cli import main


def test_list_filters_by_tag(capsys):
    main(["list", "--tag", "5080"])
    names = capsys.readouterr().out.splitlines()
    assert "tum-halle" not in names
    assert all(name.startswith("nc-11-") for name in names)
    assert len(names) == 10


def test_list_no_filter_includes_everything(capsys):
    main(["list"])
    names = capsys.readouterr().out.splitlines()
    assert len(names) == 26


def test_config_filters_by_tag(capsys):
    main(["config", "--tag", "5090"])
    output = capsys.readouterr().out
    assert "nc-9-1-1" in output
    assert "nc-11-1-1" not in output


def test_status_excludes_tum_halle_by_default(monkeypatch):
    from rechna import status

    captured = {}

    def fake_probe_all(machines_dict, max_workers=16):
        captured["names"] = set(machines_dict)
        return []

    monkeypatch.setattr(status, "probe_all", fake_probe_all)
    monkeypatch.setattr(status, "format_table", lambda statuses: "")

    main(["status"])

    assert "tum-halle" not in captured["names"]
    assert len(captured["names"]) == 25


def test_status_tag_narrows_further(monkeypatch):
    from rechna import status

    captured = {}

    def fake_probe_all(machines_dict, max_workers=16):
        captured["names"] = set(machines_dict)
        return []

    monkeypatch.setattr(status, "probe_all", fake_probe_all)
    monkeypatch.setattr(status, "format_table", lambda statuses: "")

    main(["status", "--tag", "5090"])

    assert captured["names"] == {f"nc-9-{a}-{b}" for a in range(1, 6) for b in range(1, 4)}


def test_connect_runs_ssh_with_single_machine_config(monkeypatch):
    captured = {}

    def fake_run(argv):
        captured["argv"] = argv
        captured["config_text"] = Path(argv[2]).read_text()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("rechna.cli.subprocess.run", fake_run)

    with pytest.raises(SystemExit) as exc_info:
        main(["connect", "nc-9-3-2"])

    assert exc_info.value.code == 0
    argv = captured["argv"]
    assert argv[0] == "ssh"
    assert argv[1] == "-F"
    assert argv[3] == "nc-9-3-2"
    assert argv[4:] == []
    config_text = captured["config_text"]
    assert "Host tum-halle" in config_text  # embedded, needed for ProxyJump
    assert "Host nc-9-3-2" in config_text
    assert "Host nc-9-1-1" not in config_text  # only the target machine, not all 26


def test_connect_config_file_removed_after_run(monkeypatch):
    captured = {}

    def fake_run(argv):
        captured["path"] = Path(argv[2])
        assert captured["path"].exists()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("rechna.cli.subprocess.run", fake_run)

    with pytest.raises(SystemExit):
        main(["connect", "nc-9-3-2"])

    assert not captured["path"].exists()
    assert not captured["path"].parent.exists()


def test_connect_passes_through_extra_ssh_args(monkeypatch):
    captured = {}

    def fake_run(argv):
        captured["argv"] = argv
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("rechna.cli.subprocess.run", fake_run)

    with pytest.raises(SystemExit):
        main(["connect", "nc-9-3-2", "-L", "8080:localhost:8080"])

    assert captured["argv"][-2:] == ["-L", "8080:localhost:8080"]


def test_connect_propagates_ssh_exit_code(monkeypatch):
    monkeypatch.setattr(
        "rechna.cli.subprocess.run", lambda argv: SimpleNamespace(returncode=42)
    )

    with pytest.raises(SystemExit) as exc_info:
        main(["connect", "nc-9-3-2"])

    assert exc_info.value.code == 42


def test_connect_unknown_machine_errors(capsys):
    with pytest.raises(SystemExit):
        main(["connect", "nonexistent-machine"])
    assert "nonexistent-machine" in capsys.readouterr().err
