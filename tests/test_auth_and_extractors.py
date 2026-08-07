from types import SimpleNamespace

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from auth import AuthenticationError, is_logged_in, login_flow
from extractors.new_theme import format_extraction_summary, get_all_lessons, wait_for_lesson_page


class FakeInput:
    def __init__(self):
        self.calls = []

    def press_sequentially(self, text, delay=0):
        self.calls.append((text, delay))


class FakeLoginPage:
    def __init__(self, url="https://maktabkhooneh.org/"):
        self.url = url
        self.context = SimpleNamespace(storage_state=lambda path: None)
        self.selectors = []
        self.clicked = []
        self.locators = {}

    def goto(self, url, wait_until=None):
        self.url = url

    def wait_for_load_state(self, state):
        return None

    def click(self, selector):
        self.clicked.append(selector)

    def wait_for_selector(self, selector, state=None):
        self.selectors.append((selector, state))

    def locator(self, selector):
        if selector not in self.locators:
            self.locators[selector] = FakeInput()
        return self.locators[selector]

    def wait_for_url(self, pattern, timeout=None):
        raise PlaywrightTimeoutError("not redirected")


class FakeLessonLocator:
    def __init__(self, href=None, title=None, aria_label=None, text=None):
        self._href = href
        self._title = title
        self._aria_label = aria_label
        self._text = text

    def get_attribute(self, attr):
        if attr == "href":
            return self._href
        if attr == "title":
            return self._title
        if attr == "aria-label":
            return self._aria_label
        return None

    def inner_text(self):
        return self._text or ""


class FakeLessonListLocator:
    def __init__(self, items):
        self._items = items

    def count(self):
        return len(self._items)

    def nth(self, index):
        return self._items[index]


class FakeLessonPage:
    def __init__(self, lesson_items):
        self._lesson_items = lesson_items

    def locator(self, selector):
        if selector == "#unitChapter a":
            return FakeLessonListLocator(self._lesson_items)
        raise AssertionError(f"Unexpected selector: {selector}")


def test_is_logged_in_returns_true_for_business_profile(monkeypatch):
    page = SimpleNamespace(
        url="https://maktabkhooneh.org/business",
        goto=lambda *args, **kwargs: None,
        wait_for_load_state=lambda *args, **kwargs: None,
    )

    assert is_logged_in(page) is True


def test_is_logged_in_returns_false_for_login_page(monkeypatch):
    page = SimpleNamespace(
        url="https://maktabkhooneh.org/business/login",
        goto=lambda *args, **kwargs: None,
        wait_for_load_state=lambda *args, **kwargs: None,
    )

    assert is_logged_in(page) is False


def test_login_flow_raises_when_business_redirect_does_not_happen(monkeypatch):
    monkeypatch.setattr("auth.USERNAME", "user")
    monkeypatch.setattr("auth.PASSWORD", "pass")
    page = FakeLoginPage()

    with pytest.raises(AuthenticationError):
        login_flow(page)


def test_get_all_lessons_collects_unique_paths_and_titles():
    lessons = [
        FakeLessonLocator(href="/lms/course/demo/unit/1/", title="درس اول", text="درس اول"),
        FakeLessonLocator(href="/lms/course/demo/unit/2/", aria_label="درس دوم", text="درس دوم"),
        FakeLessonLocator(href="/lms/course/demo/unit/1/", title="درس اول", text="درس اول"),
    ]
    page = FakeLessonPage(lessons)

    extracted = get_all_lessons(page)

    assert [lesson.path for lesson in extracted] == ["/lms/course/demo/unit/1/", "/lms/course/demo/unit/2/"]
    assert extracted[0].title == "درس اول"
    assert extracted[1].title == "درس دوم"


def test_wait_for_lesson_page_accepts_attached_sidebar():
    class AttachedSidebarPage:
        def __init__(self):
            self.calls = []

        def wait_for_selector(self, selector, state=None, timeout=None):
            self.calls.append((selector, state, timeout))
            if selector == "#unitChapter" and state == "attached":
                return None
            raise AssertionError("unexpected selector state")

    page = AttachedSidebarPage()

    assert wait_for_lesson_page(page, timeout=1000) is True
    assert page.calls[0][0] == "#unitChapter"
    assert page.calls[0][1] == "attached"


def test_format_extraction_summary_includes_counts():
    summary = {
        "total_lessons": 4,
        "downloaded": 2,
        "no_video": 1,
        "page_errors": 1,
        "errors": 0,
    }

    message = format_extraction_summary(summary)

    assert "4 lessons" in message
    assert "downloaded=2" in message
    assert "no_video=1" in message
    assert "page_errors=1" in message
