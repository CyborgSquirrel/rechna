"""On-demand SSH probing of machine GPU/CPU/memory/login status.

There's no monitoring agent on the lab machines, so this queries them live
over SSH: one remote bash script per machine gathers everything in a
single round-trip and prints one sentinel-prefixed, delimited line, which
we grep out of stdout (so any SSH banner/MOTD noise can't corrupt
parsing).
"""

import concurrent.futures
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .registry import Machine

SENTINEL = "RECHNA_STATUS"

_REMOTE_SCRIPT = r"""
gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total \
      --format=csv,noheader,nounits 2>/dev/null | tr '\n' ';')
read _ c1u c1n c1s c1i _ < /proc/stat
sleep 0.3
read _ c2u c2n c2s c2i _ < /proc/stat
cpu_pct=$(awk -v u1="$c1u" -v n1="$c1n" -v s1="$c1s" -v i1="$c1i" \
              -v u2="$c2u" -v n2="$c2n" -v s2="$c2s" -v i2="$c2i" \
  'BEGIN{t1=u1+n1+s1+i1; t2=u2+n2+s2+i2; dt=t2-t1; di=i2-i1;
         printf "%.0f", (dt>0 ? (1-di/dt)*100 : 0)}')
mem_pct=$(free | awk '/Mem:/ {printf "%.0f", $3/$2*100}')
users=$(who | awk '{print $1}' | sort -u | paste -sd, -)
echo "RECHNA_STATUS|${gpu}|${cpu_pct}|${mem_pct}|${users:--}"
"""


@dataclass
class MachineStatus:
    name: str
    gpus: list[tuple[float, float]]  # (utilization%, memory%) per GPU
    cpu_pct: float | None
    mem_pct: float | None
    users: list[str]
    error: str | None = None


def _parse_line(name: str, line: str) -> MachineStatus:
    _, gpu_field, cpu_field, mem_field, users_field = line.split("|", 4)

    gpus = []
    for entry in gpu_field.strip(";").split(";"):
        entry = entry.strip()
        if not entry:
            continue
        util_str, used_str, total_str = (part.strip() for part in entry.split(","))
        util = float(util_str)
        total = float(total_str)
        mem_pct = (float(used_str) / total * 100) if total > 0 else 0.0
        gpus.append((util, mem_pct))

    users = [] if users_field == "-" else users_field.split(",")

    return MachineStatus(
        name=name,
        gpus=gpus,
        cpu_pct=float(cpu_field),
        mem_pct=float(mem_field),
        users=users,
    )


def probe_machine(machine: Machine, timeout: float = 8.0) -> MachineStatus:
    """Run the remote probe script on ``machine`` over SSH.

    Never raises: any connection failure, timeout, or unparseable output
    produces a ``MachineStatus`` with ``error`` set instead, so one dead
    machine doesn't take down a `status` run over all of them.
    """
    env = os.environ.copy()
    env.pop("SHELL", None)

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "ssh_config"
            config_path.write_text(machine.config)
            result = subprocess.run(
                [
                    "ssh",
                    "-F",
                    str(config_path),
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=5",
                    # BatchMode disables prompts entirely, so a host key
                    # ssh hasn't seen before would otherwise just fail the
                    # connection outright rather than asking. accept-new
                    # auto-trusts a *new* host (first-contact TOFU, same
                    # as answering "yes" to the interactive prompt
                    # `connect` would show) but still refuses a host whose
                    # key later *changes*, which stays a hard failure.
                    "-o",
                    "StrictHostKeyChecking=accept-new",
                    machine.name,
                    _REMOTE_SCRIPT,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return MachineStatus(machine.name, [], None, None, [], error="unreachable")

    for line in result.stdout.splitlines():
        if line.startswith(f"{SENTINEL}|"):
            try:
                return _parse_line(machine.name, line)
            except (ValueError, IndexError):
                return MachineStatus(
                    machine.name, [], None, None, [], error="bad response"
                )

    return MachineStatus(machine.name, [], None, None, [], error="unreachable")


def probe_all(
    machines: dict[str, Machine], max_workers: int = 16
) -> list[MachineStatus]:
    """Probe every machine concurrently, returning results in name order."""
    names = sorted(machines)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = dict(
            zip(names, pool.map(lambda n: probe_machine(machines[n]), names))
        )
    return [results[name] for name in names]


def _format_gpu_field(gpus: list[tuple[float, float]], index: int) -> str:
    if not gpus:
        return "-"
    return ",".join(f"{util:.0f}%" if index == 0 else f"{mem:.0f}%" for util, mem in gpus)


def format_table(statuses: list[MachineStatus]) -> str:
    headers = ["MACHINE", "GPU%", "GPU MEM%", "CPU%", "CPU MEM%", "USERS"]
    rows = []
    for status in statuses:
        if status.error is not None:
            rows.append([status.name, "-", "-", "-", "-", f"({status.error})"])
            continue
        rows.append(
            [
                status.name,
                _format_gpu_field(status.gpus, 0),
                _format_gpu_field(status.gpus, 1),
                f"{status.cpu_pct:.0f}%" if status.cpu_pct is not None else "-",
                f"{status.mem_pct:.0f}%" if status.mem_pct is not None else "-",
                ",".join(status.users) if status.users else "-",
            ]
        )

    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths))]
    for row in rows:
        lines.append("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    return "\n".join(lines)
