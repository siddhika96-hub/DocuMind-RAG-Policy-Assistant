import re
from pypdf import PdfReader
from docx import Document as DocxDocument
import requests
from bs4 import BeautifulSoup

def clean_text(raw: str) -> str:
    noise_patterns = [
        r"Page \d+",
    ]
    cleaned = raw
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"\n{2,}(?=[a-z])", " ", cleaned)
    return cleaned.strip()


def extract_pages(pdf_path: str) -> list[dict]:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text()
        cleaned = clean_text(raw)
        pages.append({"text": cleaned, "page_number": i + 1})
    return pages

def extract_docx_pages(docx_path: str) -> list[dict]:
    doc = DocxDocument(docx_path)
    full_text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    cleaned = clean_text(full_text)
    return [{"text": cleaned, "page_number": None}]


def extract_txt_pages(txt_path: str) -> list[dict]:
    with open(txt_path, "r", encoding="utf-8") as f:
        raw = f.read()
    cleaned = clean_text(raw)
    return [{"text": cleaned, "page_number": None}]

def extract_url_pages(url: str) -> list[dict]:
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    raw_text = soup.get_text(separator="\n")
    cleaned = clean_text(raw_text)

    return [{"text": cleaned, "page_number": None}]

SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "system override",
    "you are now",
    "disregard the above",
    "new instructions:",
    "reveal your system prompt",
    "reveal your instructions",
]


def flag_suspicious_content(text: str) -> list[str]:
    """Returns a list of suspicious phrases found, if any. Doesn't block ingestion —
    just flags it for awareness, since false positives (legitimate documents that
    happen to mention these phrases) are possible and blocking outright is too aggressive."""
    text_lower = text.lower()
    found = [phrase for phrase in SUSPICIOUS_PATTERNS if phrase in text_lower]
    return found