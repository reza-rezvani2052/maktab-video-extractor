"""Copy the Playwright Chromium runtime into the PyInstaller output folder."""

import os
import shutil
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_NAME = "Maktab-Video-Extractor"
DIST = ROOT_DIR / "dist" / APP_NAME
TARGET = DIST / "ms-playwright"
REQUIRED_BROWSER_PREFIXES = ("chromium-", "chromium_headless_shell-", "ffmpeg-")


def find_browser() -> Path:
    candidates = []
    browser_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if browser_path and browser_path != "0":
        candidates.append(Path(browser_path))

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "ms-playwright")
    candidates.extend((
        Path.home() / "AppData/Local/ms-playwright",
        Path.home() / ".cache/ms-playwright",
    ))

    for path in candidates:
        if path.is_dir() and any(path.glob("chromium-*")):
            return path

    raise FileNotFoundError(
        "Playwright Chromium was not found. Run:\n"
        f"    {sys.executable} -m playwright install chromium"
    )


def required_runtime_dirs(source: Path) -> list[Path]:
    """Return the Chromium, headless-shell, and ffmpeg directories Playwright needs."""
    directories = [
        path for path in source.iterdir()
        if path.is_dir() and path.name.startswith(REQUIRED_BROWSER_PREFIXES)
    ]
    missing = [
        prefix for prefix in REQUIRED_BROWSER_PREFIXES
        if not any(path.name.startswith(prefix) for path in directories)
    ]
    if missing:
        raise FileNotFoundError(
            f"Required Playwright runtime is missing ({', '.join(missing)}). Run:\n"
            f"    {sys.executable} -m playwright install chromium"
        )
    return directories


def main() -> None:
    source = find_browser()
    runtime_dirs = required_runtime_dirs(source)

    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    print(f"Copying bundled Chromium runtime from:\n{source}\n")
    for runtime_dir in runtime_dirs:
        shutil.copytree(runtime_dir, TARGET / runtime_dir.name)

    print(f"Done. Bundled: {', '.join(path.name for path in runtime_dirs)}")


if __name__ == "__main__":
    main()
