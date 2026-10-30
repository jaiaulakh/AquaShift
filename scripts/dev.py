"""AquaShift dev server — starts backend + frontend together."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def main() -> None:
    """Launch both servers and wait for Ctrl+C."""
    procs: list[subprocess.Popen] = []

    try:
        # Backend
        venv_python = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / "python"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        backend = subprocess.Popen(
            [
                str(venv_python), "-X", "utf8", "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload",
            ],
            cwd=str(BACKEND_DIR),
            env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
        )
        procs.append(backend)
        print("[dev] Backend starting on http://localhost:8000")

        # Frontend
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
            cwd=str(FRONTEND_DIR),
        )
        procs.append(frontend)
        print("[dev] Frontend starting on http://localhost:5173")

        print("[dev] Press Ctrl+C to stop both servers.\n")

        # Wait for either to exit
        while all(p.poll() is None for p in procs):
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[dev] Shutting down...")
    finally:
        for p in procs:
            try:
                if os.name == "nt":
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass
        for p in procs:
            p.wait(timeout=5)
        print("[dev] Stopped.")


if __name__ == "__main__":
    main()
