"""Runs a real `ato build` against generated `.ato` source -- this is the
actual ground truth for every generation attempt, the same "generate,
then verify against a real compiler" pattern verified manually during
this feature's research phase.

Requires the real `atopile` CLI to be installed and on PATH (see
requirements.txt / README -- this backend shells out to a real
subprocess, it does not reimplement any part of atopile itself).
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ATO_LIB_DIR = Path(__file__).parent / "ato_lib"

ATO_YAML = """ato-version: ^0.2.0

paths:
    src: '.'
    layout: ./layouts

builds:
    default:
        entry: circuit.ato:Circuit
"""


@dataclass
class BuildResult:
    success: bool
    stdout: str
    stderr: str
    bom_csv: str | None = None
    warnings: list[str] = field(default_factory=list)


def build_circuit(ato_source: str, timeout_s: float = 60.0) -> BuildResult:
    """Writes ato_source plus a vendored copy of ato_lib/ into a fresh
    temp project directory, runs a real `ato build` against it, and
    returns the real result -- pass/fail exactly as atopile itself
    reports it, not a heuristic or a parsed guess."""
    if not shutil.which("ato"):
        raise RuntimeError(
            "The 'ato' CLI is not installed/on PATH. Install it (see README) before calling build_circuit."
        )

    with tempfile.TemporaryDirectory(prefix="ato_build_") as tmp:
        project = Path(tmp)
        (project / "circuit.ato").write_text(ato_source)
        (project / "ato.yaml").write_text(ATO_YAML)
        shutil.copytree(ATO_LIB_DIR, project / "ato_lib")

        proc = subprocess.run(
            ["ato", "--non-interactive", "build"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        bom_csv = None
        bom_path = project / "build" / "default.csv"
        if bom_path.exists():
            bom_csv = bom_path.read_text()

        warnings = [
            line.strip()
            for line in (proc.stdout + proc.stderr).splitlines()
            if "WARNING" in line
        ]

        return BuildResult(
            success=proc.returncode == 0,
            stdout=proc.stdout,
            stderr=proc.stderr,
            bom_csv=bom_csv,
            warnings=warnings,
        )
