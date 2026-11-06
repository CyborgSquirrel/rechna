"""User-specific settings (CIT username, SSH key) loaded from a TOML file.

The file lives at ``$XDG_CONFIG_HOME/rechna/config.toml`` (falling back to
``~/.config/rechna/config.toml``) and looks like::

    username = "your-cit-username"
    identity_file = "~/.ssh/id_ed25519"
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_EXAMPLE = """\
username = "your-cit-username"
identity_file = "~/.ssh/id_ed25519"
"""


class ConfigError(Exception):
    """The user config file is missing or unusable."""


@dataclass(frozen=True)
class Settings:
    username: str
    identity_file: str


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "rechna" / "config.toml"


def load() -> Settings:
    path = config_path()
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError:
        raise ConfigError(
            f"no config file at {path}; create it with:\n\n{_EXAMPLE}"
        ) from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"invalid TOML in {path}: {e}") from None

    values = {}
    for key in ("username", "identity_file"):
        value = data.get(key)
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{path}: missing or non-string {key!r}")
        values[key] = value
    return Settings(**values)
