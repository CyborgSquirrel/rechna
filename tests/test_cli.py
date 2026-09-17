from pathlib import Path

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


def test_connect_execs_ssh_with_single_machine_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("rechna.cli.os.execvp", lambda *a: calls.append(a))
    monkeypatch.setattr("rechna.cli.tempfile.gettempdir", lambda: str(tmp_path))

    main(["connect", "nc-9-3-2"])

    assert len(calls) == 1
    program, argv = calls[0]
    assert program == "ssh"
    assert argv[0] == "ssh"
    assert argv[1] == "-F"
    config_text = Path(argv[2]).read_text()
    assert "Host tum-halle" in config_text  # embedded, needed for ProxyJump
    assert "Host nc-9-3-2" in config_text
    assert "Host nc-9-1-1" not in config_text  # only the target machine, not all 26
    assert argv[3] == "nc-9-3-2"
    assert argv[4:] == []


def test_connect_passes_through_extra_ssh_args(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("rechna.cli.os.execvp", lambda *a: calls.append(a))
    monkeypatch.setattr("rechna.cli.tempfile.gettempdir", lambda: str(tmp_path))

    main(["connect", "nc-9-3-2", "-L", "8080:localhost:8080"])

    _, argv = calls[0]
    assert argv[-2:] == ["-L", "8080:localhost:8080"]


def test_connect_unknown_machine_errors(capsys):
    with pytest.raises(SystemExit):
        main(["connect", "nonexistent-machine"])
    assert "nonexistent-machine" in capsys.readouterr().err
