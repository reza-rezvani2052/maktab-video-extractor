![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Playwright](https://img.shields.io/badge/Playwright-Latest-green)
![Purpose](https://img.shields.io/badge/Purpose-Educational-orange)

# Maktabkhooneh Video Link Extractor

A Python script that automatically logs into **Maktabkhooneh**, opens a
course, traverses every lesson, extracts the direct **HQ video URLs**,
and saves them to a text file.

> **Educational purpose only.** Please respect Maktabkhooneh's Terms of
> Service and copyright policies.

---

## Features

- Automatic login using credentials stored in a `.env` file
- Session persistence using Playwright storage_state to avoid repeated logins
- Automatically detects and supports both the legacy and the new Maktabkhooneh website themes
- Automatically starts from the first lesson of a course
- Supports both **"جلسه اول"** and **"ثبت‌نام"** buttons
- Traverses all chapters and lessons through the course sidebar
- Extracts direct HQ video URLs
- Preserves the original lesson order
- Beautiful console output powered by **Rich** (colors, panels, and spinners)
- Headless mode for automation and servers
- Supports both **interactive** and **command-line** execution
- Graceful handling of URLs without `https://`
- Uses delayed typing to provide more human-like input behavior
- Customizable output file via the `--output` option
- Verbose mode for detailed execution logs
- Saves operational and error logs to `logs/app.log` for troubleshooting
- Automatically detects expired sessions and performs a new login
- Extracts signed CDN video URLs directly from the HTML5 video player
- Downloads each video immediately after extracting its signed URL
- Names downloaded files using their lesson number and title

---

## Supported Website Themes

The extractor automatically detects the website layout and selects the
appropriate extraction strategy.

- Legacy Maktabkhooneh theme
- New Maktabkhooneh theme

No user configuration is required.

---

## Requirements

- Python 3.11+
- Playwright
- Chromium browser (installed by Playwright)

---

## Installation

```bash
git clone https://github.com/reza-rezvani2052/maktab-video-extractor.git

cd maktab-video-extractor

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

---

## Configuration

Create a `.env` file in the project root:

```env
MAKTAB_USERNAME=your_email_or_phone
MAKTAB_PASSWORD=your_password
```

After the first successful login, the script automatically creates
`maktab_state.json`, which stores the authenticated browser session
for future runs.

---

## Usage

### Interactive Mode

```bash
python main.py
```

Enter the course URL when prompted.

The script will:

1.  Log in (or reuse a saved session)
2.  Open the first lesson
3.  Traverse every lesson
4.  Extract HQ video URLs
5.  Save them into the specified output file (default: links.txt)

### Command-Line Mode

You can also provide the course URL and options directly:

```bash
python main.py [URL] [OPTIONS]
```

#### Arguments

| Argument | Description                                                                             |
| -------- | --------------------------------------------------------------------------------------- |
| `url`    | Course page URL (optional). If omitted, you will be prompted to enter it interactively. |

---

#### Options

| Option          | Description                                                               |
| --------------- | ------------------------------------------------------------------------- |
| `--version`     | Display the application version and exit.                                 |
| `--headless`    | Run the browser in headless mode without opening a browser window.        |
| `--output FILE` | Specify the output file path. Default: `links.txt`.                       |
| `--download-dir DIR` | Directory for downloaded videos. Default: `downloads`.                 |
| `--verbose`     | Display detailed progress messages, including login and navigation steps. |

---

### Examples

```bash
# Interactive mode
python main.py

# Display the application version
python main.py --version

# Interactive mode with a custom output file
python main.py --output videos.txt

# Command-line mode
python main.py "https://maktabkhooneh.org/course/..." --verbose

# Headless mode
python main.py "https://maktabkhooneh.org/course/..." --headless

# URL without the https:// prefix
python main.py "maktabkhooneh.org/course/..." --headless

# Full example: custom output file and verbose mode
python main.py "https://maktabkhooneh.org/course/..." --output course1.txt --verbose
```

---

## Project Structure

```text
.
├── extractors/
│   ├── old_theme.py       # Extractor for the legacy Maktabkhooneh theme
│   └── new_theme.py       # Extractor for the new Maktabkhooneh theme
├── main.py                # Entry point and automatic theme detection
├── requirements.txt
├── README.md
├── .env
└── maktab_state.json
```

> **Note:** `main.py` automatically detects whether the course uses the legacy or the new Maktabkhooneh theme and delegates the extraction process to the appropriate module.
>
> **Note:** `maktab_state.json` is generated automatically after the first successful login and is used to reuse the authenticated session.
>
> **Note:** `.env` stores login credentials and should not be committed to the repository.

## Technologies

- Python
- Playwright
- Rich
- python-dotenv

---

> Note: Extracted video URLs are temporary signed CDN URLs and may expire after a limited time.

## Disclaimer

This project is provided for educational purposes only.

Users are responsible for complying with Maktabkhooneh's Terms of Service and applicable copyright laws.
