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


def wait_for_lesson_page(page, timeout=15000):
    """Wait until the lesson sidebar is present, even if it is hidden but attached."""
    try:
        page.wait_for_selector("#unitChapter", state="attached", timeout=timeout)
        return True
    except TimeoutError:
        return False


def format_extraction_summary(summary):
    """Create a compact human-readable summary of extraction results."""
    return (
        f"Extraction summary: {summary['total_lessons']} lessons, "
        f"downloaded={summary['downloaded']}, no_video={summary['no_video']}, "
        f"page_errors={summary['page_errors']}, errors={summary['errors']}"
    )


def extract_new_theme(page, *, download_dir: Path, verbose=False, download=True):
    """Extract and optionally download each lesson before navigating to the next one."""
    download_links = []
    lessons = get_all_lessons(page)
    console.print(f"Lessons found: {len(lessons)}", style="green")

    if not lessons:
        console.print("No lessons found.", style="yellow")
        return download_links

    summary = {
        "total_lessons": len(lessons),
        "downloaded": 0,
        "no_video": 0,
        "page_errors": 0,
        "errors": 0,
    }

    for index, lesson in enumerate(lessons, start=1):
        lesson_url = urljoin(MAIN_URL, lesson.path)
        console.print(f"\n[{index}/{len(lessons)}] {lesson.title}", style="blue")

        if index > 1:
            page.goto(lesson_url, wait_until="domcontentloaded")
            if not wait_for_lesson_page(page, timeout=15000):
                summary["page_errors"] += 1
                console.print("Could not confirm that the lesson page is ready; skipping this lesson.", style="yellow")
                continue
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except TimeoutError:
                pass

        video_urls = extract_video_urls(page)
        if not video_urls:
            summary["no_video"] += 1
            console.print("No video found", style="yellow")
            continue

        hq_url = video_urls[0]
        download_links.append(hq_url)
        if download:
            download_index = len(download_links)
            if not download_video(hq_url, lesson.title, download_index, download_dir):
                summary["errors"] += 1
                console.print("The lesson was not downloaded; continuing with the next lesson.", style="yellow")
                continue
            summary["downloaded"] += 1
        else:
            summary["downloaded"] += 1

    console.print(format_extraction_summary(summary), style="cyan")
    return download_links
