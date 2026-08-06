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

BUILD_MODE = "--onedir"

BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_FILE = Path(f"{APP_NAME}.spec")


def remove(path: Path):
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def clean():
    print("Cleaning previous build...")

    remove(BUILD_DIR)
    remove(DIST_DIR)
    remove(SPEC_FILE)


def version(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def show_versions():
    print(f"Python      : {sys.version.split()[0]}")
    print(f"PyInstaller : {version([sys.executable, '-m', 'PyInstaller', '--version'])}")
    print(f"Playwright  : {version([sys.executable, '-m', 'playwright', '--version'])}")


def build():

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        BUILD_MODE,
        "--clean",
        "--noconfirm",
        "--collect-all",
        "playwright",
        f"--icon={ICON}",
        f"--name={APP_NAME}",
        ENTRY_POINT,
    ]

    subprocess.run(command, check=True)


def bundle_browser():
    subprocess.run(
        [sys.executable, "bundle_playwright.py"],
        check=True,
    )


def validate_bundle():
    browser_dir = DIST_DIR / APP_NAME / "ms-playwright"
    chromium_executables = list(browser_dir.glob("chromium-*/chrome-win*/chrome.exe"))
    headless_executables = list(
        browser_dir.glob("chromium_headless_shell-*/chrome-headless-shell-win64/chrome-headless-shell.exe")
    )
    if not chromium_executables or not headless_executables:
        raise FileNotFoundError(
            "The executable was built, but its bundled Chromium runtime is incomplete."
        )
    print(f"Validated bundled Chromium: {chromium_executables[0]}")


def main():

    start = time.perf_counter()

    print("Starting build...\n")

    show_versions()

    clean()

    build()

    bundle_browser()

    validate_bundle()

    elapsed = time.perf_counter() - start

    print(f"\nDone in {elapsed:.1f} seconds.")


if __name__ == "__main__":
    main()
