"""Host group definitions for the TUM CIT GPU lab.

Your CIT username and SSH key path come from the user config file; see
``rechna.settings``. They are read when a group runs, not at import time.
"""

from . import settings
from .registry import group


def _tum_halle_block(cfg: settings.Settings) -> str:
    return f"""\
Host tum-halle
    HostName halle.cit.tum.de
    User {cfg.username}
    IdentityFile {cfg.identity_file}
    IdentitiesOnly yes
    ObscureKeystrokeTiming no
"""


@group
def nc_9_5090():
    """5090 nodes: nc-9-<1-5>-<1-3>."""
    cfg = settings.load()
    yield "tum-halle", _tum_halle_block(cfg), ()
    for a in range(1, 6):
        for b in range(1, 4):
            name = f"nc-9-{a}-{b}"
            own_block = f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {cfg.username}
    ProxyJump tum-halle
    IdentityFile {cfg.identity_file}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
"""
            # tum-halle is embedded so this single machine's config is
            # self-sufficient (usable on its own with `ssh -F`).
            yield name, _tum_halle_block(cfg) + "\n" + own_block, ("5090",)


@group
def nc_11_5080():
    """5080 nodes: nc-11-<1-2>-<1-5>."""
    cfg = settings.load()
    yield "tum-halle", _tum_halle_block(cfg), ()
    for a in range(1, 3):
        for b in range(1, 6):
            name = f"nc-11-{a}-{b}"
            own_block = f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {cfg.username}
    ProxyJump tum-halle
    IdentityFile {cfg.identity_file}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
"""
            yield name, _tum_halle_block(cfg) + "\n" + own_block, ("5080",)
