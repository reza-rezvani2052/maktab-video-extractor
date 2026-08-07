from pathlib import Path
from urllib.parse import urljoin

from config import MAIN_URL, console
from downloader import download_video


def extract_old_theme(page, *, download_dir: Path, verbose=False, download=True):
    """Extract and optionally download videos from the legacy course layout."""
    download_links = []

    def vprint(*args, **kwargs):
        if verbose:
            console.print(*args, **kwargs)

    def get_current_lesson_title(video_index):
        current_link = page.locator('a.desktop-unit-nav__unit:has(.color-violet)').first
        if current_link.count() == 0:
            return f"Lesson {video_index}"

        title = (
            current_link.get_attribute("title")
            or current_link.get_attribute("aria-label")
            or current_link.inner_text()
            or f"Lesson {video_index}"
        )
        return " ".join(title.split())

    def get_next_lesson_url():
        current_link = page.locator('a.desktop-unit-nav__unit:has(.color-violet)')
        if current_link.count() == 0:
            console.print("Could not locate the current lesson in the sidebar.", style="red")
            return None

        next_link = current_link.locator(
            'xpath=following-sibling::a[contains(@class, "desktop-unit-nav__unit")]'
        ).first
        if next_link.count() > 0:
            return next_link.get_attribute("href")

        current_chapter_body = current_link.locator('xpath=ancestor::div[contains(@class, "filler")]')
        if current_chapter_body.count() == 0:
            return None

        next_chapter_title = current_chapter_body.locator(
            'xpath=following-sibling::div[contains(@class, "desktop-unit-nav__chapter")]'
        ).first
        if next_chapter_title.count() == 0:
            return None

        chapter_id = next_chapter_title.get_attribute("data-collapsible-id")
        body = page.locator(f'div.js-collapsible__body[data-collapsible-id="{chapter_id}"]')
        if body.count() > 0:
            if "js-collapsible__body--active" not in (body.get_attribute("class") or ""):
                next_chapter_title.click()
            first_unit = body.locator("a.desktop-unit-nav__unit").first
            if first_unit.count() > 0:
                first_unit.wait_for(state="visible", timeout=10000)
                return first_unit.get_attribute("href")
        return None

    while True:
        video_urls = page.eval_on_selector_all(
            "video#lecture-video source", "els => els.map(el => el.src)"
        )
        if video_urls:
            hq_url = video_urls[0]
            download_links.append(hq_url)
            video_index = len(download_links)
            title = get_current_lesson_title(video_index)
            console.print(f"Video {video_index}: {title}", style="cyan")
            if download:
                download_video(hq_url, title, video_index, download_dir)
        else:
            vprint("This lesson does not contain a video.", style="yellow")

        next_path = get_next_lesson_url()
        if not next_path:
            console.print("Reached the end of the course!", style="bold green")
            break

        next_url = urljoin(MAIN_URL, next_path) if next_path.startswith("/") else next_path
        vprint(f"Next lesson: {next_url}")
        page.goto(next_url, wait_until="domcontentloaded")
        page.wait_for_selector("div.desktop-unit-nav", timeout=10000)

    return download_links
