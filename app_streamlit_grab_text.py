#!/usr/bin/env python3
# Usage: streamlit run app_streamlit_grab_text.py
import io
import re
import time
import zipfile
from dataclasses import dataclass, asdict
from typing import Iterable, List, Tuple
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup, Comment

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StreamlitTextGrabber/1.1)"}
TIMEOUT = 30
MAX_LINKS = 10

@dataclass
class Row:
    url: str
    title: str
    text: str
    notes: str

# -------------------- Visible text extraction --------------------
def is_hidden(el) -> bool:
    style = (el.get("style") or "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    aria_hidden = (el.get("aria-hidden") or "").lower()
    if aria_hidden == "true":
        return True
    if el.has_attr("hidden"):
        return True
    return False

def visible_text_nodes(soup: BeautifulSoup) -> Iterable[str]:
    # Remove unwanted tags entirely
    for bad in soup(["script", "style", "noscript", "template"]):
        bad.decompose()

    # Remove comments
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    for el in soup.find_all(text=True):
        parent = el.parent
        if parent and is_hidden(parent):
            continue
        txt = str(el)
        if not txt or not txt.strip():
            continue
        yield txt

def extract_all_visible_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title and soup.title.string else ""
    parts: List[str] = []
    for t in visible_text_nodes(soup):
        parts.append(t)
    full = "\n".join(p.strip() for p in parts if p.strip())
    full = full.replace("\u00A0", " ")
    full = re.sub(r"[ \t]+", " ", full)
    full = re.sub(r"\n{3,}", "\n\n", full).strip()
    return title, full

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return r.text

def safe_name(idx: int, url: str) -> str:
    p = urlparse(url)
    host = (p.netloc or "site").replace(":", "_")
    tail = (p.path.strip("/") or "index").replace("/", "_")
    q = p.query.strip()
    if q:
        tail = f"{tail}_{re.sub(r'[^A-Za-z0-9]+','_',q)[:24].strip('_')}"
    return f"{idx:02d}_{host}_{tail or 'index'}.txt"

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Grab All Page Text → TXT/CSV", layout="wide")
st.title("🗂️ Grab All Visible Page Text → TXT & CSV (Streamlit)")

st.markdown(
    "Paste up to **10 URLs** below. The app will fetch each page, gather **all visible text**, "
    "then let you download a **CSV**, a **ZIP** of per‑URL `.txt` files, a **combined `.txt`**, "
    "and **individual `.txt`** per page."
)

urls_text = st.text_area(
    "Enter URLs (one per line, up to 10)",
    height=160,
    placeholder=(
        "https://partnerhelp.netflixstudios.com/hc/en-us/sections/360012197873-Branded-Delivery-Specifications\n"
        "https://example.com\n"
        "https://example.org/page"
    ),
)
delay = st.number_input("Polite delay per URL (seconds)", min_value=0.0, value=0.3, step=0.1)
start = st.button("🚀 Grab Text", type="primary")
progress = st.progress(0, text="Idle")

if start:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    urls = list(dict.fromkeys(urls))[:MAX_LINKS]
    if not urls:
        st.error("Please provide at least one valid URL.")
        st.stop()

    rows: List[Row] = []
    total = len(urls)
    for i, u in enumerate(urls, start=1):
        notes = ""
        try:
            html = fetch_html(u)
            title, text = extract_all_visible_text(html)
            rows.append(Row(url=u, title=title, text=text, notes=notes))
        except Exception as e:
            rows.append(Row(url=u, title="", text="", notes=f"Error: {e}"))
        progress.progress(i/total, text=f"Processed {i}/{total}")
        time.sleep(max(0.0, delay))

    df = pd.DataFrame([asdict(r) for r in rows])
    st.success("Done. Preview below.")
    st.dataframe(df[["title","url","notes"]], use_container_width=True, height=320)

    # CSV download (url, title, text)
    st.download_button(
        "⬇️ Download CSV (url, title, text)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="pages.csv",
        mime="text/csv",
    )

    # ZIP of per-URL .txt
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        for idx, r in enumerate(rows, start=1):
            fname = safe_name(idx, r.url)
            z.writestr(fname, r.text or "")
    zip_buf.seek(0)
    st.download_button(
        "⬇️ Download all .txt as ZIP",
        data=zip_buf,
        file_name="pages_txt.zip",
        mime="application/zip",
    )

    # NEW: Combined .txt (all pages concatenated with headers)
    combined_parts = []
    for idx, r in enumerate(rows, start=1):
        header = f"===== [{idx}] {r.title or '(no title)'} :: {r.url} =====\n"
        combined_parts.append(header + (r.text or "") + "\n\n")
    combined_txt = "".join(combined_parts).strip()
    st.download_button(
        "⬇️ Download combined .txt (all pages)",
        data=combined_txt.encode("utf-8"),
        file_name="combined_pages.txt",
        mime="text/plain",
    )

    # NEW: Individual .txt buttons per page
    with st.expander("⬇️ Download individual .txt per page"):
        for idx, r in enumerate(rows, start=1):
            fname = safe_name(idx, r.url)
            st.download_button(
                f"Download {fname}",
                data=(r.text or "").encode("utf-8"),
                file_name=fname,
                mime="text/plain",
                key=f"dl_{idx}",
            )

    st.caption("Note: This captures only **visible** text. For JS-rendered content, we can switch to a headless browser (Playwright).")
