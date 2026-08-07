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
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError, sync_playwright
from rich.panel import Panel

from auth import AuthenticationError, is_logged_in, login_flow
from config import SESSION_FILE, USERNAME, PASSWORD, console
from extractors.new_theme import extract_new_theme
from extractors.old_theme import extract_old_theme


APP_NAME = "Maktab Video Extractor(MVE)"
APP_VERSION = "2.2.0"
APP_DIRECTORY = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
LOG_FILE = APP_DIRECTORY / "logs" / "app.log"


def configure_logging() -> logging.Logger:
    """Write application activity to a support-friendly log file."""
    logger = logging.getLogger("maktab_video_extractor")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    return logger


logger = configure_logging()


START_LESSON_SELECTOR = (
    '#continueCourseNewVersion, button:has-text("ثبت نام"), '
    'button:has-text("ثبت‌نام")'
)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract HQ video links from Maktabkhooneh courses.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
        help="Show the application version and exit",
    )
    parser.add_argument("url", nargs="?", help="Course page URL")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output", default="links.txt", help="Output file path (default: links.txt)")
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory for downloaded new-theme videos (default: downloads)",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Extract only video links and skip downloading video files",
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress messages")
    return parser.parse_args()


def configure_playwright() -> Path | None:
    """Point a packaged application at its bundled Playwright browsers."""
    if getattr(sys, "frozen", False):
        browsers_path = Path(sys.executable).resolve().parent / "ms-playwright"
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
        return browsers_path
    return None


def bundled_browser_is_available(browsers_path: Path | None) -> bool:
    """Show a customer-friendly error if the packaged browser was moved or removed."""
    if browsers_path is None:
        return True

    chromium_executables = list(browsers_path.glob("chromium-*/chrome-win*/chrome.exe"))
    if chromium_executables:
        return True

    console.print(
        "[bold red]The bundled Chromium browser is missing or incomplete.[/bold red]\n\n"
        "The folder [bold]ms-playwright[/bold] must keep this exact name and be next to the .exe file.\n"
        "Copy the entire application output folder, not only the .exe file.\n\n"
        f"Expected path:\n{browsers_path}",
        style="red",
    )
    logger.error("Bundled Chromium is missing or incomplete: %s", browsers_path)
    return False


def normalize_course_url(value: str) -> str | None:
    """Return a valid Maktabkhooneh course/lesson URL, or None."""
    url = value.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    valid_hosts = {"maktabkhooneh.org", "www.maktabkhooneh.org"}
    valid_paths = ("/course/", "/lms/course/")
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.hostname not in valid_hosts:
        return None
    if not parsed.path.startswith(valid_paths):
        return None
    return url


def is_course_page_accessible(page, response, course_url: str) -> tuple[bool, str | None]:
    """Validate that the course page is actually accessible and not an error page."""
    if response is None:
        return False, "The course page did not return a valid response."

    status = response.status
    if status >= 400:
        return False, f"Course page returned HTTP status {status}."

    current_url = page.url.lower()
    if "login" in current_url and current_url != course_url.lower():
        return False, "Course page redirected to the login page; the lesson is not accessible with the current session."

    body_text = ""
    try:
        body_text = page.locator("body").inner_text(default="").lower()
    except Exception:
        pass

    if "مشکلی در سرور وجود دارد" in body_text:
        return False, "The site returned a server error page for this course."
    if "دوره حذف شده" in body_text or "دوره حذف‌شده" in body_text:
        return False, "The requested course appears to have been removed or deleted."
    if "صفحه پیدا نشد" in body_text or "page not found" in body_text or "404" in body_text:
        return False, "The course page appears to be missing or returned a 404 page."

    return True, None


def pause_before_exit() -> None:
    """Keep an executable launched by double-click open long enough to read output."""
    if not getattr(sys, "frozen", False) or "--headless" in sys.argv:
        return
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    args = parse_args()
    console.print(f"[bold cyan]{APP_NAME} v{APP_VERSION}[/bold cyan]")
    logger.info("Application started: version=%s, headless=%s", APP_VERSION, args.headless)
    if not USERNAME or not PASSWORD:
        console.print("MAKTAB_USERNAME or MAKTAB_PASSWORD not found in .env", style="red")
        logger.error("Application credentials are not configured")
        return 2

    def vprint(*values, **kwargs):
        if args.verbose:
            console.print(*values, **kwargs)

    if args.headless and not args.url:
        console.print("A course URL is required in headless mode.", style="red")
        logger.error("Headless mode was started without a course URL")
        return 2
    raw_course_url = args.url or input("\nEnter course URL:\n")
    course_url = normalize_course_url(raw_course_url)
    if not course_url:
        console.print(
            "Enter a valid Maktabkhooneh course or lesson URL.\n"
            "Examples:\n"
            "  maktabkhooneh.org/course/...\n"
            "  maktabkhooneh.org/lms/course/...",
            style="red",
        )
        logger.warning("Rejected invalid course URL input")
        return 2
    if not raw_course_url.startswith(("http://", "https://")):
        vprint(f"Added scheme -> {course_url}", style="cyan")

    browsers_path = configure_playwright()
    if not bundled_browser_is_available(browsers_path):
        return 1

    context = None
    browser = None

    with sync_playwright() as playwright:
        try:
            # Do not use channel="chrome": the packaged application ships its
            # own Playwright Chromium and must not depend on system Chrome.
            logger.info("Launching bundled Chromium")
            browser = playwright.chromium.launch(headless=args.headless)

            if Path(SESSION_FILE).exists():
                console.print("Loading saved session...", style="cyan")
                logger.info("Loading saved session")
                context = browser.new_context(storage_state=SESSION_FILE)
                page = context.new_page()
                if is_logged_in(page):
                    console.print("Session is still valid. No need to log in again.", style="green")
                    logger.info("Saved session is valid")
                else:
                    console.print("Session expired. Logging in again...", style="yellow")
                    logger.info("Saved session expired; starting login")
                    context.close()
                    context = browser.new_context()
                    page = context.new_page()
                    login_flow(page)
            else:
                logger.info("No saved session; starting login")
                context = browser.new_context()
                page = context.new_page()
                login_flow(page)

            console.print(f"Opening course:\n{course_url}", style="cyan")
            logger.info("Opening course URL: %s", course_url)
            response = page.goto(course_url, wait_until="domcontentloaded")

            accessible, error_message = is_course_page_accessible(page, response, course_url)
            if not accessible:
                console.print(error_message, style="red")
                logger.error("Course page validation failed: %s", error_message)
                return 1

            try:
                page.wait_for_selector(START_LESSON_SELECTOR, timeout=15000)
            except TimeoutError:
                console.print("Start lesson button was not found.", style="red")
                logger.error("Start lesson button was not found")
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
                    logger.error("Could not find a start lesson button")
                    return 1
                register_button.click()
                vprint("Navigated to the first lesson.", style="green")

            try:
                page.wait_for_selector("div.desktop-unit-nav, #unitChapter", timeout=15000)
            except TimeoutError:
                console.print("Sidebar not found after clicking start.", style="red")
                logger.error("Sidebar was not found after opening the first lesson")
                return 1

            if page.locator("#unitChapter").count() > 0:
                console.print("New theme detected", style="green")
                logger.info("Detected new website theme")
                download_links = extract_new_theme(
                    page,
                    download_dir=Path(args.download_dir),
                    verbose=args.verbose,
                    download=not args.no_download,
                )
            elif page.locator(".desktop-unit-nav").count() > 0:
                console.print("Old theme detected", style="green")
                logger.info("Detected old website theme")
                download_links = extract_old_theme(
                    page,
                    download_dir=Path(args.download_dir),
                    verbose=args.verbose,
                    download=not args.no_download,
                )
            else:
                console.print("Unknown theme. Cannot extract.", style="red")
                logger.error("Could not detect a supported website theme")
                return 1

            if not download_links:
                console.print("No video links extracted.", style="yellow")
                logger.warning("No video links were extracted")
                return 1

            links_text = "\n".join(download_links)
            with open(args.output, "w", encoding="utf-8") as output_file:
                output_file.write(links_text)
            console.print(Panel(links_text, title=f"{len(download_links)} Video Links", border_style="blue"))
            console.print(f"Successfully saved {len(download_links)} links to {args.output}", style="green")
            logger.info("Successfully saved %d video links to %s", len(download_links), args.output)

            return 0

        except AuthenticationError as error:
            console.print(f"Login failed: {error}", style="red")
            logger.exception("Login failed")
            return 1
        except TimeoutError as error:
            console.print(f"Timed out while interacting with the website: {error}", style="red")
            logger.exception("Timed out while interacting with the website")
            return 1
        except PlaywrightError as error:
            console.print(f"Browser operation failed: {error}", style="red")
            logger.exception("Browser operation failed")
            return 1
        finally:
            if context:
                context.close()
            if browser:
                browser.close()


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        console.print("\nOperation cancelled.", style="yellow")
        logger.warning("Operation cancelled by user")
        exit_code = 130
    except Exception as error:
        console.print(f"Unexpected error: {error}", style="red")
        logger.exception("Unexpected unhandled error")
        exit_code = 1
    finally:
        pause_before_exit()
    raise SystemExit(exit_code)
