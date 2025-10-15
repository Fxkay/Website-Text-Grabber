# web2txt

Streamlit app that **extracts all visible text** from up to **10 URLs** and lets you **download** results as **CSV** or **TXT** (per-page, combined, or zipped).

## Features
- Paste up to 10 URLs (one per line)
- Captures visible text (headings, paragraphs, lists, tables, link text)
- Downloads: **CSV**, **per-page .txt**, **combined .txt**, **ZIP of .txt**
- Simple, fast, no headless browser

## Quick Start
```bash
git clone <your-repo-url>
cd <repo>
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements_streamlit_grab_text.txt
streamlit run app_streamlit_grab_text.py
```

## Usage
1. Paste up to **10** URLs (one per line).
2. Click **Grab Text**.
3. Download your preferred format:
   - `pages.csv` (url, title, text)
   - **Combined** `.txt` (all pages)
   - **Per-page** `.txt` files
   - **ZIP** with all `.txt`

## Notes
- Extracts **visible** text only (scripts/styles/hidden elements removed).
- For heavily **JS-rendered** pages, consider a Playwright/Puppeteer version.

## Files
- `app_streamlit_grab_text.py` — Streamlit app
- `requirements_streamlit_grab_text.txt` — dependencies

## License
MIT (update as needed)
