"""Prepare colour figures, compile LaTeX, and validate four pages without a separate cover."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_latex_report.py")], check=True, cwd=ROOT)
    local = ROOT / ".runtime/tectonic/tectonic.exe"
    compiler = str(local) if local.exists() else shutil.which("tectonic")
    if compiler is None:
        raise SystemExit("Install Tectonic, or compile report/230145E_a02.tex with a LaTeX installation.")
    destination = ROOT / "output/pdf"
    destination.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault("TECTONIC_CACHE_DIR", str(ROOT / ".runtime/tectonic-cache"))
    subprocess.run([compiler, "--keep-logs", "--outdir", str(destination), "230145E_a02.tex"],
                   check=True, cwd=ROOT / "report", env=environment)
    subprocess.run([sys.executable, str(ROOT / "scripts/verify_report.py")], check=True, cwd=ROOT)
    print(f"LaTeX report ready: {destination / '230145E_a02.pdf'}")


if __name__ == "__main__":
    main()
