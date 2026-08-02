from urllib.parse import urljoin
from playwright.sync_api import TimeoutError
from config import MAIN_URL, console


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
                timeout=timeout
                )
        return True
    except TimeoutError:
        return False


def extract_video_urls(page):
    if not wait_for_video(page):
        console.print("No video tag found yet.")
        return []

    urls = page.evaluate(
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
    return urls


def get_all_lessons(page):
    lessons = page.locator("#unitChapter a")
    urls = []
    for i in range(lessons.count()):
        href = lessons.nth(i).get_attribute("href")
        if href and "/unit/" in href and href not in urls:
            urls.append(href)
    return urls


def extract_new_theme(page, *, verbose=False):
    download_links = []

    lesson_paths = get_all_lessons(page)
    console.print(f"Lessons found: {len(lesson_paths)}", style="green")

    if not lesson_paths:
        console.print("No lessons found.", style="yellow")
        return download_links

    for index, lesson_path in enumerate(lesson_paths):
        lesson_url = urljoin(MAIN_URL, lesson_path)
        console.print(f"\n[{index + 1}/{len(lesson_paths)}] {lesson_url}", style="blue")

        if index > 0:
            page.goto(lesson_url, wait_until="domcontentloaded")
            try:
                page.wait_for_selector("#unitChapter", timeout=15000)
            except Exception as e:
                console.print(f"Error loading lesson: {e}", style="red")
                continue

        video_urls = extract_video_urls(page)
        if video_urls:
            hq_url = video_urls[0]
            if hq_url not in download_links:
                download_links.append(hq_url)
            console.print(f"🎬 {hq_url}", style="green")
        else:
            console.print("⚠️ No video found", style="yellow")

    return download_links
