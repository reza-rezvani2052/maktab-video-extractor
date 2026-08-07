"""Download signed video URLs while they are still valid."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from config import MAIN_URL, console


INVALID_FILENAME_CHARS = set('<>:"/\\|?*')
CHUNK_SIZE = 1024 * 1024


def strip_duration_suffix(title: str) -> str:
    """Remove trailing video duration labels such as 'ویدئو 2 دقیقه' or 'ویدئو 1 ساعت و 5 دقیقه'."""
    pattern = re.compile(
        r"(?ix)"
        r"(?:\s|[._-])*(?:ویدئو|video)\s*"
        r"(?:"
        r"(?:\d+|[۰-۹]+)\s*(?:ساعت|hours?|hrs?|h)"
        r"(?:\s*(?:و|and)\s*)?"
        r")?"
        r"(?:"
        r"(?:\d+|[۰-۹]+)\s*(?:دقیقه|min|minutes?)"
        r")?"
        r"\s*$",
        re.UNICODE,
    )
    return pattern.sub("", title).strip(" .")


def safe_filename(title: str, index: int) -> str:
    """Return a Windows-safe, ordered filename for a lesson."""
    cleaned_title = strip_duration_suffix(title)
    cleaned_title = "".join(
        " " if char in INVALID_FILENAME_CHARS or ord(char) < 32 else char for char in cleaned_title
    )
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip(" .")
    cleaned_title = cleaned_title[:180] or f"Lesson {index}"
    return f"{index}- {cleaned_title}.mp4"


def download_video(url: str, title: str, index: int, download_dir: Path) -> Path | None:
    """Download one video before its signed URL expires.

    An incomplete download remains as a ``.part`` file. A later call using a
    newly extracted URL resumes it when the CDN supports range requests.
    """
    download_dir.mkdir(parents=True, exist_ok=True)
    destination = download_dir / safe_filename(title, index)
    partial_path = destination.with_suffix(destination.suffix + ".part")

    if destination.exists():
        console.print(f"Already downloaded: {destination.name}", style="yellow")
        return destination

    offset = partial_path.stat().st_size if partial_path.exists() else 0
    headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{MAIN_URL}/"}
    if offset:
        headers["Range"] = f"bytes={offset}-"

    try:
        response = urlopen(Request(url, headers=headers), timeout=60)
        status = getattr(response, "status", response.getcode())
        if offset and status != 206:
            offset = 0
            partial_path.unlink(missing_ok=True)
            response.close()
            response = urlopen(
                Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": f"{MAIN_URL}/"}),
                timeout=60,
            )

        content_length = response.headers.get("Content-Length")
        total = offset + int(content_length) if content_length and content_length.isdigit() else None
        mode = "ab" if offset else "wb"

        with response, Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(f"Downloading {index}- {title}", total=total, completed=offset)
            with partial_path.open(mode) as output_file:
                while chunk := response.read(CHUNK_SIZE):
                    output_file.write(chunk)
                    progress.update(task_id, advance=len(chunk))

        partial_path.replace(destination)
        console.print(f"Saved: {destination}", style="green")
        return destination
    except (HTTPError, URLError, OSError, TimeoutError) as error:
        console.print(f"Download failed for '{title}': {error}", style="red")
        return None
