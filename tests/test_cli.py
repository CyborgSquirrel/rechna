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
