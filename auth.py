from playwright.sync_api import TimeoutError
from config import MAIN_URL, PROFILE_URL, SESSION_FILE, LOAD_STATE, console, USERNAME, PASSWORD


class AuthenticationError(RuntimeError):
    """Raised when Maktabkhooneh does not confirm a successful login."""


def login_flow(page):
    """ورود کامل با مودال و ذخیره‌سازی سشن"""
    console.print("Starting login process...", style="bold blue")
    page.goto(MAIN_URL, wait_until="domcontentloaded")
    page.wait_for_load_state(LOAD_STATE)
    page.click("#login")
    page.wait_for_selector("#tessera", state="visible")
    page.locator("#tessera").press_sequentially(USERNAME, delay=100)
    console.print("Username entered.", style="cyan")
    page.click('[data-tag="ga-email-phone-login"]')
    page.wait_for_selector("#password", state="visible")
    page.locator("#password").press_sequentially(PASSWORD, delay=100)
    console.print("Password entered.", style="cyan")
    page.click('[data-tag="ga-password-submit"]')
    console.print('Clicked "Login" button. Waiting for completion...', style="cyan")
    try:
        page.wait_for_url("**/business**", timeout=15000)
    except TimeoutError as error:
        raise AuthenticationError("Login was not confirmed: the profile page did not open.") from error

    if not is_logged_in(page):
        raise AuthenticationError("Login was not confirmed: the saved session is not authenticated.")

    page.context.storage_state(path=SESSION_FILE)
    console.print("✔ Login successful. Session saved.", style="green")


def is_logged_in(page):
    """بررسی اعتبار سشن با مراجعه به PROFILE_URL"""
    page.goto(PROFILE_URL)
    page.wait_for_load_state(LOAD_STATE)
    profile_url = PROFILE_URL.rstrip("/")
    current_url = page.url.rstrip("/")
    return current_url.startswith(profile_url) and "login" not in current_url.lower()
