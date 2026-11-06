import pytest

from rechna import settings
from rechna.cli import main
from rechna.registry import all_machines


def test_config_path_respects_xdg_config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert settings.config_path() == tmp_path / "rechna" / "config.toml"


def test_config_path_defaults_to_dot_config(tmp_path, monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setattr(settings.Path, "home", lambda: tmp_path)
    assert settings.config_path() == tmp_path / ".config" / "rechna" / "config.toml"


def test_values_flow_into_machine_configs():
    config = all_machines()["nc-9-1-1"].config
    assert "User testuser" in config
    assert "IdentityFile ~/.ssh/test_key" in config


def test_missing_file_explains_how_to_create_it(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
    with pytest.raises(settings.ConfigError, match="username ="):
        settings.load()


def test_missing_key_is_an_error():
    settings.config_path().write_text('username = "x"\n')
    with pytest.raises(settings.ConfigError, match="identity_file"):
        settings.load()


def test_invalid_toml_is_an_error():
    settings.config_path().write_text("username = \n")
    with pytest.raises(settings.ConfigError, match="invalid TOML"):
        settings.load()


def test_cli_reports_config_error_and_exits_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
    with pytest.raises(SystemExit) as exc:
        main(["list"])
    assert exc.value.code == 1
    assert "no config file" in capsys.readouterr().err
