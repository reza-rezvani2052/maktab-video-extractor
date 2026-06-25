import os
import time
from urllib.parse import urljoin

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError

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
PROFILE_URL = "https://maktabkhooneh.org/dashboard/courses/"

# LOAD_STATE = "networkidle"   # NOTE: این روش یک خط در میون کار میکرد
LOAD_STATE = "domcontentloaded"

# ...

# میتوان از ست به جای لیست برای جلوگیری از ذخیره شدن لینک های تکراری استفاده کرد
# اما در ست نباید روی ترتیب عناصر حساب باز کرد و چون ترتیب دانلود لینک ها برای من
# مهم است، نمیتوانم از ست استفاده کنم
# download_links = set()
# download_links.add(hq_url)
download_links = []


# ...

def login_flow(page):
    """تمام مراحل ورود را با مودال انجام می‌دهد و state را ذخیره می‌کند"""
    print("Starting login process...")

    # رفتن به صفحه‌ی اصلی که دکمه‌ی "ورود | ثبت‌نام" را دارد
    page.goto(MAIN_URL)
    # page.wait_for_load_state("networkidle") # NOTE: این روش یک خط ذر میون کار میکنه
    page.wait_for_load_state(LOAD_STATE)

    # کلیک روی دکمه‌ی "ورود | ثبت‌نام"
    # سلکتور: id="login"
    page.click("#login")
    # print("روی دکمهٔ «ورود | ثبت‌نام» کلیک شد.")
    print('Clicked "Login / Register" button.')

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
    print("Username entered.")
    time.sleep(2)

    #  کلیک روی دکمهٔ «تایید»
    #  HTML: data-tag="ga-email-phone-login"
    page.click('[data-tag="ga-email-phone-login"]')
    print('Clicked "Confirm" button.')

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
    print("Password entered.")

    #  کلیک روی دکمهٔ «ورود»
    #  HTML: data-tag="ga-password-submit"
    page.click('[data-tag="ga-password-submit"]')
    print('Clicked "Login" button. Waiting for completion...')

    #  صبر میکنیم تا لاگین کامل شود (مودال بسته شود یا به داشبورد برود)
    #  یک راه: صبر میکنیم تا URL تغییر کند یا یک المنت خاص ظاهر شود
    #  اینجا ۱۵ ثانیه صبر می‌کنیم تا به PROFILE_URL ریدایرکت شویم
    try:
        page.wait_for_url(PROFILE_URL, timeout=15000)
    except TimeoutError:
        # شاید ریدایرکت به صفحه‌ای دیگر باشد، مهم نیست
        print("Timeout: Redirect to profile did not happen.")
    except Exception as e:
        print(f"Error: {e}")
    # except:
    #     pass  # Code Smell  # NOTE: ***

    #  ذخیره‌سازی سشن
    page.context.storage_state(path=SESSION_FILE)
    print("✔ Login successful. Session saved.")


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

def get_next_lesson_url(page):
    """
    با توجه به sidebar صفحه درس فعلی، لینک درس بعدی را پیدا می‌کند.
    اگر به پایان دوره برسیم None برمی‌گرداند.
    """
    # پیدا کردن لینک درس جاری (با کلاس color-violet)
    current_link = page.locator('a.desktop-unit-nav__unit:has(.color-violet)')
    if current_link.count() == 0:
        print("❌ Could not locate the current lesson in the sidebar.")
        return None

    #  تلاش برای گرفتن sibling بعدی در همان فصل
    next_link = current_link.locator(
            'xpath=following-sibling::a[contains(@class, "desktop-unit-nav__unit")]'
            ).first
    if next_link.count() > 0:
        return next_link.get_attribute('href')

    #  به فصل بعدی برو
    # از لینک فعلی برو به div.filler (والد مجموعهٔ درس‌های فصل)
    current_chapter_body = current_link.locator(
            'xpath=ancestor::div[contains(@class, "filler")]'
            )
    if current_chapter_body.count() == 0:
        return None

    # فصل بعدی: sibling بعدی از نوع desktop-unit-nav__chapter
    next_chapter_title = current_chapter_body.locator(
            'xpath=following-sibling::div[contains(@class, "desktop-unit-nav__chapter")]'
            ).first  # <--- همین جا .first اضافه شد

    if next_chapter_title.count() == 0:
        return None  # فصل بعدی وجود ندارد -> پایان دوره

    # باز کردن فصل اگر بسته باشد
    chapter_id = next_chapter_title.get_attribute('data-collapsible-id')
    body = page.locator(f'div.js-collapsible__body[data-collapsible-id="{chapter_id}"]')
    if body.count() > 0:
        if 'js-collapsible__body--active' not in (body.get_attribute('class') or ''):
            # کلیک روی عنوان فصل برای باز شدن
            next_chapter_title.click()
            # کمی صبر برای انیمیشن باز شدن
            # time.sleep(0.5)
            time.sleep(1)

        # اولین درس داخل این فصل
        first_unit = body.locator('a.desktop-unit-nav__unit').first
        if first_unit.count() > 0:
            return first_unit.get_attribute('href')

    return None


# ...

def main():
    with sync_playwright() as p:
        # NOTE: *
        # اگر همه چیز تست شده، می‌توان headless=True کرد تا اجرا سریع‌تر و بی‌صدا شود
        browser = p.chromium.launch(headless=False)

        # مدیریت لاگین (با ذخیره و بازیابی سشن)
        if os.path.exists(SESSION_FILE):
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            if is_logged_in(page):
                print("✅ Session is still valid. No need to log in again.")
            else:
                print("⚠️ Session expired. Logging in again...")
                page.close()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                login_flow(page)
        else:
            context = browser.new_context()
            page = context.new_page()
            login_flow(page)

        # دریافت آدرس دوره از کاربر
        course_url = input("\nEnter course URL:\n").strip()
        if not course_url:
            print("No course URL provided. Exiting.")
            browser.close()
            return

        # رفتن به صفحهٔ دوره
        page.goto(course_url)
        # صبر می‌کنیم تا حداقل یکی از دو دکمهٔ «جلسه اول» یا «ثبت‌نام» ظاهر شود
        page.wait_for_selector(
                '#continueCourseNewVersion, button:has-text("ثبت نام"), button:has-text("ثبت‌نام")',
                timeout=10000
                )
        print(f"Course page loaded: {course_url}")

        # کلیک روی دکمهٔ مناسب
        try:
            # اولویت با دکمهٔ «جلسه اول» (id مشخص) – .first برای جلوگیری از خطای strict mode
            """
            بعضی از صفحات مکتب‌خونه دو نسخه از دکمه‌ی «جلسه اول» دارند (یکی برای نمای دسکتاپ و یکی برای نمای موبایل)
            و هر دو دارای id="continueCourseNewVersion" هستند.
            با .first فقط اولین عنصر انتخاب می‌شود و خطا برطرف می‌گردد
            """
            first_lesson_btn = page.locator('#continueCourseNewVersion').first
            if first_lesson_btn.count() > 0:
                first_lesson_btn.click()
                print("✅ Navigated to the first lesson (via 'جلسه اول' button).")
            else:
                # دکمهٔ «ثبت‌نام» را امتحان کن
                register_btn = page.locator('button:has-text("ثبت نام"), button:has-text("ثبت‌نام")').first
                if register_btn.count() > 0:
                    register_btn.click()
                    print("✅ Navigated to the first lesson (via 'ثبت‌نام' button).")
                else:
                    print("⚠️ Start button not found. Continuing anyway...")

            # بعد از کلیک، منتظر ظاهر شدن سایدبار (حداکثر ۱۰ ثانیه)
            page.wait_for_selector('div.desktop-unit-nav', timeout=10000)
            print("✅ Sidebar loaded – ready to extract videos.")
        except Exception as e:
            print(f"Failed to click start button: {e}")
            browser.close()
            return

        # حالا که در اولین درس هستیم، پیمایش درس‌ها را شروع کن
        print("\nStarting lesson traversal and video extraction...\n")

        while True:
            # استخراج لینک ویدئوی کیفیت بالا (HQ)
            video_urls = page.eval_on_selector_all(
                    'video#lecture-video source', 'els => els.map(el => el.src)'
                    )
            if video_urls:
                hq_url = video_urls[0]  # معمولاً اولین source کیفیت HQ است
                # print(f"🎬 HQ video: {hq_url}")
                print(f"{hq_url}")
                download_links.append(hq_url)
            else:
                print("⚠️ This lesson does not contain a video.")

            # پیدا کردن لینک درس بعدی در sidebar
            next_path = get_next_lesson_url(page)
            if not next_path:
                print("🏁 Reached the end of the course!")
                break

            # ساخت آدرس کامل
            if next_path.startswith('/'):
                # next_url = f"https://maktabkhooneh.org{next_path}"  # ok
                next_url = urljoin(MAIN_URL, next_path)  # این روش حرفه‌ای‌تر و مطمئن‌تر است :
            else:
                next_url = next_path

            print(f"Next lesson: ➡️{next_url}")

            page.goto(next_url)
            # page.wait_for_load_state(LOAD_STATE)
            page.wait_for_selector('div.desktop-unit-nav', timeout=10000)
            time.sleep(0.3)

        # ...

        print(" ------------------------------------- ")
        print("Video Links:")
        for link in download_links:
            print(f"{link}")
        with open('links.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(download_links))
            # f.write(os.linesep.join(download_links))  #  ???
            print(f"{len(download_links)} links saved to links.txt")
        print(" ------------------------------------- ")

        # ...

        # پایان
        input("\n\nDone. Press Enter to exit...")
        browser.close()


# ...

if __name__ == "__main__":
    main()
