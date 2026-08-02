"""
Build executable using PyInstaller.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import time

APP_NAME = "Maktab-Video-Extractor"
ENTRY_POINT = "main.py"
ICON = Path("RC") / "app-icon.ico"

BUILD_MODE = "--onedir"          # or "--onefile"

BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_FILE = Path(f"{APP_NAME}.spec")


def remove(path: Path):
    """Delete a file or directory if it exists."""
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def clean():
    """Clean previous build artifacts."""
    print("Cleaning previous build...")

    remove(BUILD_DIR)
    remove(DIST_DIR)
    remove(SPEC_FILE)


def show_pyinstaller_version():
    """Print PyInstaller version."""
    result = subprocess.run(
        ["pyinstaller", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )

    print(f"PyInstaller {result.stdout.strip()}")


def build():
    """Run PyInstaller."""

    command = [
        "pyinstaller",
        BUILD_MODE,
        f"--icon={ICON}",
        f"--name={APP_NAME}",
        ENTRY_POINT,
    ]

    subprocess.run(command, check=True)


def main():
    start = time.perf_counter()

    print("Starting build...\n")

    show_pyinstaller_version()
    clean()
    build()

    elapsed = time.perf_counter() - start

    print(f"\nBuild completed successfully in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed (exit code {e.returncode}).")
        sys.exit(e.returncode)