import os

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

USERNAME = os.getenv("MAKTAB_USERNAME", "").strip()
PASSWORD = os.getenv("MAKTAB_PASSWORD", "").strip()

MAIN_URL = "https://maktabkhooneh.org"
PROFILE_URL = "https://maktabkhooneh.org/business"  # فقط کاربران لاگین‌شده به این صفحه دسترسی دارند
SESSION_FILE = "maktab_state.json"
LOAD_STATE = "domcontentloaded"

console = Console()
