from downloader import safe_filename
from main import normalize_course_url, parse_args
import sys


def test_normalize_course_url_adds_https_scheme():
    assert normalize_course_url("maktabkhooneh.org/course/demo/") == "https://maktabkhooneh.org/course/demo/"


def test_normalize_course_url_accepts_lms_course_urls():
    assert normalize_course_url("https://www.maktabkhooneh.org/lms/course/demo/") == "https://www.maktabkhooneh.org/lms/course/demo/"


def test_normalize_course_url_rejects_non_maktab_host():
    assert normalize_course_url("https://example.com/course/demo/") is None


def test_normalize_course_url_rejects_non_course_path():
    assert normalize_course_url("https://maktabkhooneh.org/profile") is None


def test_safe_filename_replaces_invalid_path_characters():
    assert safe_filename('درس/عنوان: "test"?', 7) == "7- درس عنوان test.mp4"


def test_parse_args_supports_no_download(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "https://maktabkhooneh.org/course/demo/", "--no-download"])
    args = parse_args()
    assert args.no_download is True
    assert args.url == "https://maktabkhooneh.org/course/demo/"
