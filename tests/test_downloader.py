from downloader import safe_filename


def test_removes_persian_video_duration_suffix():
    title = "این دوره چیه و برای چه کسانیه؟ ویدئو 2 دقیقه"
    assert safe_filename(title, 1) == "1- این دوره چیه و برای چه کسانیه؟.mp4"


def test_removes_video_duration_suffix_without_space():
    title = "آموزش ساخت اکانت Nano Banana - دسترسی به نسخه رایگان ویدئو4 دقیقه"
    assert safe_filename(title, 2) == "2- آموزش ساخت اکانت Nano Banana - دسترسی به نسخه رایگان.mp4"


def test_removes_hour_and_minute_suffix():
    title = "بهینه سازی و تنظیم مدل ویدئو 1 ساعت و 5 دقیقه"
    assert safe_filename(title, 3) == "3- بهینه سازی و تنظیم مدل.mp4"
