# old theme style :
# آدرس صفحه معرفی دوره آموزشی :
# maktabkhooneh.org/course/آموزش-طراحی-سرویس-fastapi-mk10645/
# آدرس صفحه درس اول دوره آموزشی :
# maktabkhooneh.org/course/آموزش-طراحی-سرویس-fastapi-mk10645/مقدمه-آشنایی-دوره-ch26665/ویدیو-آشنایی-دوره/

# new theme style
# آدرس صفحه درس اول دوره آموزشی :
# maktabkhooneh.org/course/آموزش-tailwind-css-4-3-mk16455/
# # آدرس صفحه درس اول دوره آموزشی :
# maktabkhooneh.org/lms/course/آموزش-tailwind-css-4-3-mk16455/unit/227239/

# --------------------------------------------------------------------------------------

import argparse  # noqa: I001
import os

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError, sync_playwright
from rich.panel import Panel

from auth import AuthenticationError, is_logged_in, login_flow
from config import SESSION_FILE, USERNAME, PASSWORD, console
from extractors.new_theme import extract_new_theme
from extractors.old_theme import extract_old_theme


START_LESSON_SELECTOR = (
    '#continueCourseNewVersion, button:has-text("ثبت نام"), '
    'button:has-text("ثبت‌نام")'
)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract HQ video links from Maktabkhooneh courses.")
    parser.add_argument("url", nargs="?", help="Course page URL")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output", default="links.txt", help="Output file path (default: links.txt)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress messages")
    return parser.parse_args()


def main():
    args = parse_args()
    if not USERNAME or not PASSWORD:
        console.print("MAKTAB_USERNAME or MAKTAB_PASSWORD not found in .env", style="red")
        return 2

    def vprint(*values, **kwargs):
        if args.verbose:
            console.print(*values, **kwargs)

    if args.headless and not args.url:
        console.print("A course URL is required in headless mode.", style="red")
        return 2
    course_url = args.url or input("\nEnter course URL:\n").strip()
    if not course_url:
        console.print("No course URL provided. Exiting.", style="red")
        return 1
    if not course_url.startswith(("http://", "https://")):
        course_url = "https://" + course_url
        vprint(f"Added scheme -> {course_url}", style="cyan")

    context = None
    browser = None

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=args.headless)

            if os.path.exists(SESSION_FILE):
                console.print("Loading saved session...", style="cyan")
                context = browser.new_context(storage_state=SESSION_FILE)
                page = context.new_page()
                if is_logged_in(page):
                    console.print("Session is still valid. No need to log in again.", style="green")
                else:
                    console.print("Session expired. Logging in again...", style="yellow")
                    context.close()
                    context = browser.new_context()
                    page = context.new_page()
                    login_flow(page)
            else:
                context = browser.new_context()
                page = context.new_page()
                login_flow(page)

            console.print(f"Opening course:\n{course_url}", style="cyan")
            page.goto(course_url, wait_until="domcontentloaded")

            try:
                page.wait_for_selector(START_LESSON_SELECTOR, timeout=15000)
            except TimeoutError:
                console.print("Start lesson button was not found.", style="red")
                return 1

            first_lesson = page.locator("#continueCourseNewVersion").first
            if first_lesson.count() > 0:
                first_lesson.click()
                vprint("Clicked first lesson button.", style="green")
            else:
                register_button = page.locator(
                    'button:has-text("ثبت نام"), button:has-text("ثبت‌نام")'
                ).first
                if register_button.count() == 0:
                    console.print("Cannot find start lesson button.", style="red")
                    return 1
                register_button.click()
                vprint("Navigated to the first lesson.", style="green")

            try:
                page.wait_for_selector("div.desktop-unit-nav, #unitChapter", timeout=15000)
            except TimeoutError:
                console.print("Sidebar not found after clicking start.", style="red")
                return 1

            if page.locator("#unitChapter").count() > 0:
                console.print("New theme detected", style="green")
                download_links = extract_new_theme(page, verbose=args.verbose)
            elif page.locator(".desktop-unit-nav").count() > 0:
                console.print("Old theme detected", style="green")
                download_links = extract_old_theme(page, verbose=args.verbose)
            else:
                console.print("Unknown theme. Cannot extract.", style="red")
                return 1

            if not download_links:
                console.print("No video links extracted.", style="yellow")
                return 1

            links_text = "\n".join(download_links)
            with open(args.output, "w", encoding="utf-8") as output_file:
                output_file.write(links_text)
            console.print(Panel(links_text, title=f"{len(download_links)} Video Links", border_style="blue"))
            console.print(f"Successfully saved {len(download_links)} links to {args.output}", style="green")

            if not args.headless:
                input("\nDone. Press Enter to exit...")
            return 0

        except AuthenticationError as error:
            console.print(f"Login failed: {error}", style="red")
            return 1
        except TimeoutError as error:
            console.print(f"Timed out while interacting with the website: {error}", style="red")
            return 1
        except PlaywrightError as error:
            console.print(f"Browser operation failed: {error}", style="red")
            return 1
        finally:
            if context:
                context.close()
            if browser:
                browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
