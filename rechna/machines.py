"""Host group definitions for the TUM CIT GPU lab.

Fill in USERNAME and IDENTITY_FILE with your real CIT username and the
path to your TUM private key before use.
"""

from .registry import group

USERNAME = "changeme"
IDENTITY_FILE = "~/.ssh/changeme"


def _tum_halle_block() -> str:
    return f"""\
Host tum-halle
    HostName halle.cit.tum.de
    User {USERNAME}
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ObscureKeystrokeTiming no
"""


@group
def nc_9_5090():
    """5090 nodes: nc-9-<1-5>-<1-3>."""
    yield "tum-halle", _tum_halle_block(), ()
    for a in range(1, 6):
        for b in range(1, 4):
            name = f"nc-9-{a}-{b}"
            own_block = f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {USERNAME}
    ProxyJump tum-halle
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
"""
            # tum-halle is embedded so this single machine's config is
            # self-sufficient (usable on its own with `ssh -F`).
            yield name, _tum_halle_block() + "\n" + own_block, ("5090",)


@group
def nc_11_5080():
    """5080 nodes: nc-11-<1-2>-<1-5>."""
    yield "tum-halle", _tum_halle_block(), ()
    for a in range(1, 3):
        for b in range(1, 6):
            name = f"nc-11-{a}-{b}"
            own_block = f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {USERNAME}
    ProxyJump tum-halle
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
"""
            yield name, _tum_halle_block() + "\n" + own_block, ("5080",)
