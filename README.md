# Maktabkhooneh Video Link Extractor

A Python script that automatically logs into **Maktabkhooneh**, opens a
course, traverses every lesson, extracts the direct **HQ video URLs**,
and saves them to a text file.

> **Educational purpose only.** Please respect Maktabkhooneh's Terms of
> Service and copyright policies.

------------------------------------------------------------------------

## Features

-   Automatic login using credentials stored in a `.env` file
-   Session persistence to avoid repeated logins
-   Automatically starts from the first lesson of a course
-   Supports both **"جلسه اول"** and **"ثبت‌نام"** buttons
-   Traverses all chapters and lessons through the course sidebar
-   Extracts direct HQ video URLs
-   Preserves the original lesson order
-   Saves all links into `links.txt`
-   Simulates human typing to reduce bot detection

------------------------------------------------------------------------

## Requirements

-   Python 3.11+
-   Playwright
-   Chromium browser (installed by Playwright)

------------------------------------------------------------------------

## Installation

``` bash
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

------------------------------------------------------------------------

## Configuration

Create a `.env` file:

``` env
MAKTAB_USERNAME=your_email_or_phone
MAKTAB_PASSWORD=your_password
```

------------------------------------------------------------------------

## Usage

``` bash
python main.py
```

Enter the course URL when prompted.

The script will:

1.  Log in (or reuse a saved session)
2.  Open the first lesson
3.  Traverse every lesson
4.  Extract HQ video URLs
5.  Save them into `links.txt`

------------------------------------------------------------------------

## Project Structure

``` text
.
├── main.py
├── .env
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Technologies

-   Python
-   Playwright
-   python-dotenv

------------------------------------------------------------------------

## License

This project is intended for educational purposes only.
