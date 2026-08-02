"""
این اسکریپت با استفاده از subprocess.run() دستور PyInstaller را اجرا می‌کند
"""

import time
import subprocess

# ...

APP_NAME = "Maktab-Video-Extractor"
ICON = "RC/app-icon.ico"
DIST_DIR = "dist/Maktab-Video-Extractor"

# ...

# دستور ساخت فایل اجرایی توسط پای اینستالر
PYINSTALLER_CMD = (
    "pyinstaller --onedir "
    f"--icon={ICON} --name={APP_NAME} main.py"
)

# ...


def run_pyinstaller():
    """اجرای PyInstaller"""
    print("Running PyInstaller...")
    result = subprocess.run(PYINSTALLER_CMD, shell=True)

    if result.returncode == 0:
        print("Build successful!")
        return True
    else:
        print("Build failed!")
        return False


if __name__ == "__main__":
    print("Starting build process...")

    start_time = time.time()
    
    # اجرای PyInstaller
    #if run_pyinstaller():
    run_pyinstaller()

    end_time = time.time()

    print(f"Build finished in {end_time - start_time:.2f} seconds.")
