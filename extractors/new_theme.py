from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError

from config import MAIN_URL, console
from downloader import download_video


@dataclass(frozen=True)
class Lesson:
    path: str
    title: str


def wait_for_video(page, timeout=30000):
    try:
        page.wait_for_function(
            """
            () => {
                const video = document.querySelector("video");
                if (!video) return false;
                return (video.src && video.src.includes(".mp4")) ||
                       (video.currentSrc && video.currentSrc.includes(".mp4"));
            }
            """,
            timeout=timeout,
        )
        return True
    except TimeoutError:
        return False


def extract_video_urls(page):
    if not wait_for_video(page):
        console.print("No video tag found yet.")
        return []

    return page.evaluate(
        """
        () => {
            const result = [];
            document.querySelectorAll("video").forEach(video => {
                if (video.src) result.push(video.src);
                if (video.currentSrc) result.push(video.currentSrc);
                video.querySelectorAll("source").forEach(source => {
                    if (source.src) result.push(source.src);
                });
            });
            return [...new Set(result)].filter(x => x.includes(".mp4"));
        }
        """
    )


def get_all_lessons(page):
    """Collect ordered lesson URLs and their sidebar titles once."""
    lessons = page.locator("#unitChapter a")
    seen_paths = set()
    result = []
    for i in range(lessons.count()):
        lesson = lessons.nth(i)
        href = lesson.get_attribute("href")
        if not href or "/unit/" not in href or href in seen_paths:
            continue

        title = lesson.get_attribute("title") or lesson.get_attribute("aria-label") or lesson.inner_text()
        title = " ".join((title or "").split())
        result.append(Lesson(path=href, title=title or f"Lesson {len(result) + 1}"))
        seen_paths.add(href)
    return result


def extract_new_theme(page, *, download_dir: Path, verbose=False):
    """Extract and download each lesson before navigating to the next one."""
    download_links = []
    lessons = get_all_lessons(page)
    console.print(f"Lessons found: {len(lessons)}", style="green")

    if not lessons:
        console.print("No lessons found.", style="yellow")
        return download_links

    for index, lesson in enumerate(lessons, start=1):
        lesson_url = urljoin(MAIN_URL, lesson.path)
        console.print(f"\n[{index}/{len(lessons)}] {lesson.title}", style="blue")

        if index > 1:
            page.goto(lesson_url, wait_until="domcontentloaded")
            try:
                page.wait_for_selector("#unitChapter", timeout=15000)
            except TimeoutError as error:
                console.print(f"Error loading lesson: {error}", style="red")
                continue

        video_urls = extract_video_urls(page)
        if not video_urls:
            console.print("No video found", style="yellow")
            continue

        hq_url = video_urls[0]
        download_links.append(hq_url)
        download_index = len(download_links)
        if not download_video(hq_url, lesson.title, download_index, download_dir):
            console.print("The lesson was not downloaded; continuing with the next lesson.", style="yellow")

    return download_links
