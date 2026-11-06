import pytest


@pytest.fixture(autouse=True)
def rechna_config(tmp_path, monkeypatch):
    """Point rechna at a throwaway user config so tests never read the real one."""
    config_dir = tmp_path / "xdg" / "rechna"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        'username = "testuser"\nidentity_file = "~/.ssh/test_key"\n'
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
