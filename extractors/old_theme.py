import time
from urllib.parse import urljoin
from config import MAIN_URL, console


def extract_old_theme(page, *, verbose=False):
    download_links = []

    def vprint(*args, **kwargs):
        if verbose:
            console.print(*args, **kwargs)

    def get_next_lesson_url(page):
        current_link = page.locator('a.desktop-unit-nav__unit:has(.color-violet)')
        if current_link.count() == 0:
            console.print("❌ Could not locate the current lesson in the sidebar.", style="red")
            return None

        next_link = current_link.locator(
                'xpath=following-sibling::a[contains(@class, "desktop-unit-nav__unit")]'
                ).first
        if next_link.count() > 0:
            return next_link.get_attribute('href')

        current_chapter_body = current_link.locator(
                'xpath=ancestor::div[contains(@class, "filler")]'
                )
        if current_chapter_body.count() == 0:
            return None

        next_chapter_title = current_chapter_body.locator(
                'xpath=following-sibling::div[contains(@class, "desktop-unit-nav__chapter")]'
                ).first
        if next_chapter_title.count() == 0:
            return None

        chapter_id = next_chapter_title.get_attribute('data-collapsible-id')
        body = page.locator(f'div.js-collapsible__body[data-collapsible-id="{chapter_id}"]')
        if body.count() > 0:
            if 'js-collapsible__body--active' not in (body.get_attribute('class') or ''):
                next_chapter_title.click()
                time.sleep(1)
            first_unit = body.locator('a.desktop-unit-nav__unit').first
            if first_unit.count() > 0:
                return first_unit.get_attribute('href')
        return None

    while True:
        video_urls = page.eval_on_selector_all(
                'video#lecture-video source', 'els => els.map(el => el.src)'
                )
        if video_urls:
            hq_url = video_urls[0]
            console.print(f"🎬 {hq_url}")
            download_links.append(hq_url)
        else:
            vprint("⚠️ This lesson does not contain a video.", style="yellow")

        next_path = get_next_lesson_url(page)
        if not next_path:
            console.print("🏁 Reached the end of the course!", style="bold green")
            break

        next_url = urljoin(MAIN_URL, next_path) if next_path.startswith('/') else next_path
        vprint(f"➡️ Next lesson: {next_url}")
        page.goto(next_url, wait_until="domcontentloaded")
        page.wait_for_selector('div.desktop-unit-nav', timeout=10000)
        time.sleep(0.3)

    return download_links
