import os  # noqa: I001
import time
import argparse
from urllib.parse import urljoin

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError

from rich.console import Console
from rich.panel import Panel
from rich.status import Status

# ...

SESSION_FILE = "maktab_state.json"

# ...

load_dotenv()

USERNAME = os.getenv("MAKTAB_USERNAME", "").strip()
PASSWORD = os.getenv("MAKTAB_PASSWORD", "").strip()

if not USERNAME or not PASSWORD:
    raise RuntimeError("MAKTAB_USERNAME or MAKTAB_PASSWORD not found in .env")

# ...

MAIN_URL = "https://maktabkhooneh.org"
PROFILE_URL = "https://maktabkhooneh.org/business"  # بعد از لاگین، به این صفحه ریدایرکت می‌شویم و می‌توانیم بررسی کنیم که لاگین موفق بوده است یا خیر

# LOAD_STATE = "networkidle"
LOAD_STATE = "domcontentloaded"

VERBOSE = False  # با دستورهای CLI تنظیم می‌شود

# ...

console = Console()


# ...

def login_flow(page):
    """تمام مراحل ورود را با مودال انجام می‌دهد و state را ذخیره می‌کند"""
    console.print("Starting login process...", style="bold blue")

    # رفتن به صفحه‌ی اصلی که دکمه‌ی "ورود | ثبت‌نام" را دارد
    # page.goto(MAIN_URL)
    page.goto(MAIN_URL, wait_until="domcontentloaded")

    # page.wait_for_load_state("networkidle") #  این روش یک خط ذر میون کار میکنه
    page.wait_for_load_state(LOAD_STATE)

    # کلیک روی دکمه‌ی "ورود | ثبت‌نام"
    # سلکتور: id="login"
    page.click("#login")
    # print("روی دکمهٔ «ورود | ثبت‌نام» کلیک شد.")
    vprint('Clicked "Login / Register" button.', style="cyan")

    #  منتظر نمایش فیلد نام کاربری در مودال
    page.wait_for_selector("#tessera", state="visible")

    # پر کردن نام کاربری (ایمیل یا شماره موبایل)
    # page.fill("#tessera", USERNAME)
    # page.type("#tessera", USERNAME, delay=100)  # هر کاراکتر 100 میلی‌ثانیه تأخیر
    # این از روش بالا جدیدتر است
    page.locator("#tessera").press_sequentially(
            USERNAME,
            delay=100
            )
    vprint("Username entered.", style="cyan")
    time.sleep(2)

    #  کلیک روی دکمهٔ «تایید»
    #  HTML: data-tag="ga-email-phone-login"
    page.click('[data-tag="ga-email-phone-login"]')
    vprint('Clicked "Confirm" button.', style="cyan")

    # یک مکث کوتاه برای شبیه‌سازی رفتار انسان
    # time.sleep(0.5)
    time.sleep(1.5)

    #  منتظر نمایش فیلد رمز عبور
    page.wait_for_selector("#password", state="visible")

    #  پر کردن رمز عبور (با تأخیر بین کاراکترها)
    # page.fill("#password", PASSWORD)
    # اگر بخواهیم تایپ رمز عبور آهسته‌تر باشد، باید به‌جای page.fill از
    # گزینه page.type با پارامتر delay استفاده کنیم:
    # page.type("#password", PASSWORD, delay=100)  # هر کاراکتر 100 میلی‌ثانیه تأخیر
    # این از روش بالا جدیدتر است
    page.locator("#password").press_sequentially(
            PASSWORD,
            delay=100
            )
    vprint("Password entered.", style="cyan")

    #  کلیک روی دکمهٔ «ورود»
    #  HTML: data-tag="ga-password-submit"
    page.click('[data-tag="ga-password-submit"]')
    vprint('Clicked "Login" button. Waiting for completion...', style="cyan")

    #  صبر میکنیم تا لاگین کامل شود (مودال بسته شود یا به داشبورد برود)
    #  یک راه: صبر میکنیم تا URL تغییر کند یا یک المنت خاص ظاهر شود
    #  اینجا ۱۵ ثانیه صبر می‌کنیم تا به PROFILE_URL ریدایرکت شویم
    try:
        page.wait_for_url(PROFILE_URL, timeout=15000)
    except TimeoutError:
        # شاید ریدایرکت به صفحه‌ای دیگر باشد، مهم نیست
        console.print("Timeout: Redirect to profile did not happen.", style="yellow")
    except Exception as e:
        console.print(f"Error: {e}", style="red")
    # except:
    #     pass  # Code Smell  # NOTE: ***

    #  ذخیره‌سازی سشن
    page.context.storage_state(path=SESSION_FILE)
    console.print("✔ Login successful. Session saved.", style="green")


# ...

def is_logged_in(page):
    """بررسی می‌کند که آیا با سشن قبلی هنوز لاگین هستیم."""
    page.goto(PROFILE_URL)
    page.wait_for_load_state(LOAD_STATE)

    # اگر در URL کلمه‌ی login وجود داشت، لاگین نیستیم
    # می‌توانیم به جای این کار، وجود یک عنصر خاص (مثلاً نام کاربری) را بررسی کنیم
    if "login" in page.url.lower():
        return False

    # TODO: *  به جای روش بالا، بهتر است وجود یک المان مخصوص کاربران لاگین‌شده را بررسی کنیم
    # if page.locator(".user-profile").count() > 0:
    #     return True
    # or: ???
    # if page.locator(".user-profile").first.wait_for(state="visible", timeout=2000):
    #     return True

    return True

# ...

def parse_args():
    parser = argparse.ArgumentParser(
            description="Extract HQ video links from Maktabkhooneh courses."
            )
    parser.add_argument(
            "url",
            nargs="?",
            help="Course page URL (e.g., https://maktabkhooneh.org/course/...)",
            )
    parser.add_argument(
            "--headless",
            action="store_true",
            help="Run browser in headless mode",
            )
    parser.add_argument(
            "--output",
            default="links.txt",
            help="Output file path (default: links.txt)",
            )
    parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed progress messages",
            )
    return parser.parse_args()

# ...

def vprint(*args, **kwargs):
    if VERBOSE:
        console.print(*args, **kwargs)

# ...

def wait_for_video(page, timeout=30000):
    try:
        page.wait_for_function(
            """
            () => {
                const video = document.querySelector("video");

                if (!video)
                    return false;

                return (
                    video.src &&
                    video.src.includes(".mp4")
                ) ||
                (
                    video.currentSrc &&
                    video.currentSrc.includes(".mp4")
                );
            }
            """,
            timeout=timeout
        )

        return True

    except TimeoutError:
        return False
   
# ...

def extract_video_urls(page):

    if not wait_for_video(page):
        console.print("No video tag found yet.")
        return []

    urls = page.evaluate(
        """
        () => {

            const result = [];

            document.querySelectorAll("video").forEach(video => {

                if(video.src)
                    result.push(video.src);

                if(video.currentSrc)
                    result.push(video.currentSrc);


                video.querySelectorAll("source").forEach(source => {

                    if(source.src)
                        result.push(source.src);

                });

            });


            return [...new Set(result)]
                .filter(
                    x => x.includes(".mp4")
                );
        }
        """
    )

    return urls

# ...

def get_all_lessons(page):
    """
    دریافت تمام لینک‌های درس‌ها از sidebar
    """
    lessons = page.locator("#unitChapter a")

    urls = []

    for i in range(lessons.count()):
        href = lessons.nth(i).get_attribute("href")

        if href and "/unit/" in href:
            if href not in urls:
                urls.append(href)

    return urls

# ...


def main():
    args = parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    # مقدار headless از CLI می‌آید
    headless = args.headless
    
    # میتوان از ست به جای لیست برای جلوگیری از ذخیره شدن لینک های تکراری استفاده کرد
    # اما در ست نباید روی ترتیب عناصر حساب باز کرد و چون ترتیب دانلود لینک ها برای من
    # مهم است، نمیتوانم از ست استفاده کنم
    # download_links = set()
    # download_links.add(hq_url)
    download_links = []

    context = None
    browser = None


    with sync_playwright() as p:

        try:
            # اجرا با headless=True موجب اجرای سریع‌تر و بی‌صدا میشود
            # و مرورگر به کاربر نشان داده نمیشود
            browser = p.chromium.launch(headless=headless)  # default is False


            # =====================================
            # Session / Login
            # =====================================
            # مدیریت لاگین (با ذخیره و بازیابی سشن)
            if os.path.exists(SESSION_FILE):
                console.print("Loading saved session...", style="cyan")

                context = browser.new_context(storage_state=SESSION_FILE)
                page = context.new_page()

                if is_logged_in(page):
                    console.print(
                            "✅ Session is still valid. No need to log in again.",
                            style="green"
                            )
                else:
                    console.print("⚠️ Session expired. Logging in again...", style="yellow")
                    # page.close()
                    context.close()
                    context = browser.new_context()
                    page = context.new_page()
                    login_flow(page)

            else:               
                context = browser.new_context()
                page = context.new_page()
                login_flow(page)



            # =====================================
            # Course URL
            # =====================================

            course_url = args.url
            if not course_url:
                # دریافت آدرس دوره از کاربر، اگر کاربر در حال تعاملی باشد
                course_url = input("\nEnter course URL:\n").strip()

            if not course_url:
                console.print("No course URL provided. Exiting.", style="red")
                # browser.close()  # TODO: ???
                return


            # اگر URL با http شروع نمی‌شود، https:// را اضافه کن
            if not course_url.startswith(('http://', 'https://')):
                course_url = 'https://' + course_url
                vprint(f"Added scheme -> {course_url}", style="cyan")


            console.print(f"Opening course:\n{course_url}", style="cyan")


            # =====================================
            # Open Course
            # =====================================
            # تلاش برای بارگذاری صفحهٔ دوره           
            try:
                page.goto(course_url, wait_until="domcontentloaded")
            except Exception as e:
                console.print(
                        f"Failed to load URL: {e}\n"
                        "Please provide a valid full URL, e.g. https://maktabkhooneh.org/course/...",
                        style="red"
                        )
                browser.close()  # TODO: ???
                return

            # صبر می‌کنیم تا حداقل یکی از دو دکمهٔ «جلسه اول» یا «ثبت‌نام» ظاهر شود
            page.wait_for_selector(
                '#continueCourseNewVersion, '
                'button:has-text("ثبت نام"), '
                'button:has-text("ثبت‌نام")',
                timeout=15000
            )
            # vprint(f"Course page loaded: {course_url}", style="blue")


            # =====================================
            # Enter first lesson
            # =====================================

            opened = False

            # اولویت با دکمهٔ «جلسه اول» (id مشخص) – .first برای جلوگیری از خطای strict mode
            """
            بعضی از صفحات مکتب‌خونه دو نسخه از دکمه‌ی «جلسه اول» دارند (یکی برای نمای دسکتاپ و یکی برای نمای موبایل)
            و هر دو دارای id="continueCourseNewVersion" هستند.
            با .first فقط اولین عنصر انتخاب می‌شود و خطا برطرف می‌گردد
            """
            first_btn = page.locator("#continueCourseNewVersion").first

            if first_btn.count() > 0:
                first_btn.click()
                opened = True

                vprint("Clicked first lesson button.", style="green")
                #vprint(
                #        "✅ Navigated to the first lesson (via 'جلسه اول' button).",
                #        style="green"
                #        )

            else:
                # دکمهٔ «ثبت‌نام» را امتحان کن
                register_btn = page.locator(
                    'button:has-text("ثبت نام"), '
                    'button:has-text("ثبت‌نام")'
                ).first

                if register_btn.count() > 0:
                    # TODO: *** این را تست کنم
                    # with Status("Navigating to first lesson...", console=console):
                    register_btn.click()
                    opened = True                                                
                    vprint("✅ Navigated to the first lesson (via 'ثبت‌نام' button).", style="green")
                else:
                    vprint("⚠️ Start button not found. Continuing anyway...", style="yellow")


            if not opened:
                console.print(
                    "Cannot find start lesson button.",
                    style="red"
                )

                return


            page.wait_for_selector(
                "#unitChapter",
                timeout=15000
            )



            # =====================================
            # Get lessons
            # =====================================

            # دریافت همه درس‌ها از sidebar
            lesson_paths = get_all_lessons(page)
            console.print(f"Lessons found: {len(lesson_paths)}", style="green")


            if not lesson_paths:
                console.print("No lessons found.", style="yellow")
                return



            # =====================================
            # Traverse lessons
            # =====================================

            for index, lesson_path in enumerate(lesson_paths):
                lesson_url = urljoin(MAIN_URL, lesson_path)

                console.print(f"\n[{index + 1}/{len(lesson_paths)}]",
                    style="blue"
                )
                console.print(lesson_url)

                # فقط از درس دوم به بعد navigate کن
                if index > 0:
                    page.goto(
                        lesson_url,
                        wait_until="domcontentloaded"
                    )


                try:
                    page.wait_for_selector("#unitChapter", timeout=15000)

                    # اجازه ساخت Player توسط Vue
                    page.wait_for_timeout(3000)

                    video_urls = extract_video_urls(page)

                    if video_urls:
                        hq_url = video_urls[0]

                        if hq_url not in download_links:
                            download_links.append(hq_url)

                        console.print(f"🎬 {hq_url}", style="green")


                    else:

                        console.print(
                            "⚠️ No video found",
                            style="yellow"
                        )



                except Exception as e:

                    console.print(
                        f"Error in lesson {index + 1}: {e}",
                        style="red"
                    )



            # =====================================
            # Save links
            # =====================================

            if download_links:
                links_text = "\n".join(download_links)

                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(links_text)

                panel = Panel(
                    links_text,
                    title=f"{len(download_links)} Video Links",
                    border_style="blue"
                )

                console.print(panel)
                console.print(
                    f"📄 Saved to {args.output}",
                    style="green"
                )

            else:
                console.print("No video links extracted.", style="yellow")

            input("\nDone. Press Enter to exit...")


        finally:
            if context:
                context.close()

            if browser:
                browser.close()
                   
# ...

if __name__ == "__main__":
    main()
