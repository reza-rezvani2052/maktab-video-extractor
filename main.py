
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

# https://chat.deepseek.com/a/chat/s/665bad35-340e-46c7-b1d8-f649d0185541

# ...

import os
import argparse
from playwright.sync_api import sync_playwright, TimeoutError
from rich.panel import Panel

from config import MAIN_URL, SESSION_FILE, console, USERNAME, PASSWORD  # از config مقادیر را می‌خوانیم
from auth import login_flow, is_logged_in
from extractors.old_theme import extract_old_theme
from extractors.new_theme import extract_new_theme

if not USERNAME or not PASSWORD:
    raise RuntimeError("MAKTAB_USERNAME or MAKTAB_PASSWORD not found in .env")

def parse_args():
    parser = argparse.ArgumentParser(description="Extract HQ video links from Maktabkhooneh courses.")
    parser.add_argument("url", nargs="?", help="Course page URL")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output", default="links.txt", help="Output file path (default: links.txt)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress messages")
    return parser.parse_args()

def main():
    args = parse_args()
    global VERBOSE
    VERBOSE = args.verbose
    headless = args.headless

    def vprint(*args, **kwargs):
        if VERBOSE:
            console.print(*args, **kwargs)

    download_links = []
    context = None
    browser = None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)

            # مدیریت سشن / لاگین
            if os.path.exists(SESSION_FILE):
                console.print("Loading saved session...", style="cyan")
                context = browser.new_context(storage_state=SESSION_FILE)
                page = context.new_page()
                if is_logged_in(page):
                    console.print("✅ Session is still valid. No need to log in again.", style="green")
                else:
                    console.print("⚠️ Session expired. Logging in again...", style="yellow")
                    context.close()
                    context = browser.new_context()
                    page = context.new_page()
                    login_flow(page)
            else:
                context = browser.new_context()
                page = context.new_page()
                login_flow(page)

            # دریافت آدرس دوره
            course_url = args.url
            if not course_url:
                course_url = input("\nEnter course URL:\n").strip()
            if not course_url:
                console.print("No course URL provided. Exiting.", style="red")
                return
            if not course_url.startswith(('http://', 'https://')):
                course_url = 'https://' + course_url
                vprint(f"Added scheme -> {course_url}", style="cyan")

            console.print(f"Opening course:\n{course_url}", style="cyan")

            try:
                page.goto(course_url, wait_until="domcontentloaded")
            except Exception as e:
                console.print(f"Failed to load URL: {e}\nPlease provide a valid full URL.", style="red")
                return

            # صبر برای دکمه شروع
            page.wait_for_selector(
                '#continueCourseNewVersion, button:has-text("ثبت نام"), button:has-text("ثبت‌نام")',
                timeout=15000
            )

            # کلیک روی دکمه شروع
            opened = False
            first_btn = page.locator("#continueCourseNewVersion").first
            if first_btn.count() > 0:
                first_btn.click()
                opened = True
                vprint("Clicked first lesson button.", style="green")
            else:
                register_btn = page.locator('button:has-text("ثبت نام"), button:has-text("ثبت‌نام")').first
                if register_btn.count() > 0:
                    register_btn.click()
                    opened = True
                    vprint("✅ Navigated to the first lesson (via 'ثبت‌نام' button).", style="green")
                else:
                    vprint("⚠️ Start button not found. Continuing anyway...", style="yellow")

            if not opened:
                console.print("Cannot find start lesson button.", style="red")
                return

            # انتظار برای ظاهر شدن سایدبار (قدیم یا جدید)
            try:
                page.wait_for_selector("div.desktop-unit-nav, #unitChapter", timeout=15000)
            except TimeoutError:
                console.print("Sidebar not found after clicking start.", style="red")
                return

            # تشخیص تم
            if page.locator("#unitChapter").count() > 0:
                theme = "new"
                console.print("✅ New theme detected", style="green")
            elif page.locator(".desktop-unit-nav").count() > 0:
                theme = "old"
                console.print("✅ Old theme detected", style="green")
            else:
                console.print("❌ Unknown theme. Cannot extract.", style="red")
                return

            # استخراج
            if theme == "old":
                download_links = extract_old_theme(page, verbose=VERBOSE)
            else:
                download_links = extract_new_theme(page, verbose=VERBOSE)

            # ذخیره‌سازی
            if download_links:
                links_text = "\n".join(download_links)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(links_text)
                panel = Panel(links_text, title=f"{len(download_links)} Video Links", border_style="blue")
                console.print(panel)
                console.print(f"📄 Successfully saved {len(download_links)} links to {args.output}", style="green")
            else:
                console.print("No video links extracted.", style="yellow")

            input("\nDone. Press Enter to exit...")

        finally:
            if context:
                context.close()
            if browser:
                browser.close()

if __name__ == "__main__":
    main()

