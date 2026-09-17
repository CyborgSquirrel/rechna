"""Host group definitions for the TUM CIT GPU lab.

Fill in USERNAME and IDENTITY_FILE with your real CIT username and the
path to your TUM private key before use.
"""

from .registry import group

USERNAME = "changeme"
IDENTITY_FILE = "~/.ssh/changeme"


def _tum_halle() -> tuple[str, str, tuple[str, ...]]:
    return (
        "tum-halle",
        f"""\
Host tum-halle
    HostName halle.cit.tum.de
    User {USERNAME}
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ObscureKeystrokeTiming no
""",
        (),
    )


@group
def nc_9_5090():
    """5090 nodes: nc-9-<1-5>-<1-3>."""
    yield _tum_halle()
    for a in range(1, 6):
        for b in range(1, 4):
            name = f"nc-9-{a}-{b}"
            yield (
                name,
                f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {USERNAME}
    ProxyJump tum-halle
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
""",
                ("5090",),
            )


@group
def nc_11_5080():
    """5080 nodes: nc-11-<1-2>-<1-5>."""
    yield _tum_halle()
    for a in range(1, 3):
        for b in range(1, 6):
            name = f"nc-11-{a}-{b}"
            yield (
                name,
                f"""\
Host {name}
    HostName {name}.kosmos.cit.tum.de
    User {USERNAME}
    ProxyJump tum-halle
    IdentityFile {IDENTITY_FILE}
    IdentitiesOnly yes
    ForwardX11 yes
    ForwardX11Trusted yes
""",
                ("5080",),
            )
