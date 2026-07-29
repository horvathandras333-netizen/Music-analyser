import subprocess
import sys
from pathlib import Path


def build():
    """Build portable LoopForge executable using PyInstaller."""
    project_dir = Path(__file__).parent.resolve()
    main_py = project_dir / "main.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "LoopForge",
        str(main_py),
    ]

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_dir, check=False)

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "LoopForge.exe"
        print(f"\nBuild successful! Executable generated at:\n{exe_path}")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
