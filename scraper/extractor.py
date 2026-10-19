import hashlib
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List

from .config import REQUEST_HEADERS, REQUEST_TIMEOUT


def compute_content_hash(text: str) -> str:
    """Compute a SHA-256 hash of normalized text content for change detection."""
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def fetch_page(url: str) -> Optional[str]:
    """Fetch raw HTML content from the given URL."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[Scraper Extractor] Failed to fetch {url}: {e}")
        return None


def extract_page_data(url: str, html: str, category: str = "course") -> Dict[str, Any]:
    """
    Extract structured content from HTML.
    Cleans boilerplate and parses semantic sections.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract meta tags
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.split("|")[0].strip()

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "noscript", "svg", "nav", "header", "footer"]):
        tag.decompose()

    # Remove modals or otp popups if present
    for elem_id in ["otp-modal", "otp-step-1", "otp-step-2", "otp-step-3", "syllabus-teaser"]:
        el = soup.find(id=elem_id)
        if el:
            el.decompose()

    # Extract all text for hashing
    clean_text = soup.get_text(" ", strip=True)
    content_hash = compute_content_hash(clean_text)

    data = {
        "url": url,
        "title": title,
        "description": meta_desc,
        "content_hash": content_hash,
        "category": category,
        "overview": [],
        "format_details": {},
        "learning_path": [],
        "highlights": [],
        "faqs": [],
        "contact_info": {},
    }

    if category == "contact":
        _extract_contact_data(soup, data)
    elif category == "about":
        _extract_about_data(soup, data)
    else:
        _extract_course_data(soup, data)

    return data


def _extract_course_data(soup: BeautifulSoup, data: Dict[str, Any]):
    """Extract structured course sections."""
    # 1. Course overview & hero details
    h1 = soup.find("h1")
    if h1:
        data["title"] = h1.get_text(strip=True)

    # Key course attributes (Format, Scope, Objective)
    for card in soup.find_all(["div", "section"]):
        text = card.get_text(" ", strip=True)
        if "Offline class learning" in text or "Format" in text:
            for item in card.find_all(["div", "p"]):
                txt = item.get_text(strip=True)
                if "Offline" in txt or "Pune" in txt:
                    data["format_details"]["format"] = txt
                elif "Scope" in txt:
                    data["format_details"]["scope"] = txt
                elif "Objective" in txt:
                    data["format_details"]["objective"] = txt

    # 2. Extract Lead / Overview Paragraphs
    main_section = soup.find("main") or soup.find("article") or soup
    paragraphs = []
    for p in main_section.find_all("p"):
        p_text = p.get_text(" ", strip=True)
        if len(p_text) > 35 and not any(skip in p_text.lower() for skip in ["cookie", "enroll now", "click here", "skip to"]):
            paragraphs.append(p_text)
    data["overview"] = paragraphs[:3]

    # 3. Extract Curriculum / Learning Path Modules
    curriculum_section = soup.find(id="curriculum") or soup.find("section", class_=re.compile(r"curriculum", re.I))
    modules = []
    if curriculum_section:
        for item in curriculum_section.find_all(["h3", "h4", "div"]):
            txt = item.get_text(strip=True)
            if txt and len(txt) < 80 and txt not in modules:
                # Filter out generic labels
                if not any(skip in txt.lower() for skip in ["module", "week", "curriculum", "syllabus", "view", "download"]):
                    modules.append(txt)
    
    # Fallback to general list items or roadmap
    if not modules:
        for ul in main_section.find_all(["ul", "ol"]):
            for li in ul.find_all("li"):
                li_text = li.get_text(strip=True)
                if 5 < len(li_text) < 100:
                    modules.append(li_text)

    data["learning_path"] = modules[:15]

    # 4. Extract FAQs if present
    faqs = []
    for faq_container in soup.find_all(["details", "div"], class_=re.compile(r"faq", re.I)):
        q = faq_container.find(["summary", "h3", "h4", "button"])
        a = faq_container.find(["p", "div"])
        if q and a:
            faqs.append({
                "question": q.get_text(strip=True),
                "answer": a.get_text(strip=True)
            })
    data["faqs"] = faqs


def _extract_contact_data(soup: BeautifulSoup, data: Dict[str, Any]):
    """Extract contact information (phone, whatsapp, email, address)."""
    contact = {
        "phone": "+91 87931 00815",
        "whatsapp": "+91 87931 00815",
        "email": "chetan2469@gmail.com",
        "location": "Pune, Maharashtra, India",
        "website": "https://www.chedo.in/"
    }

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "tel:" in href:
            contact["phone"] = href.replace("tel:", "").strip()
        elif "mailto:" in href:
            contact["email"] = href.replace("mailto:", "").strip()
        elif "wa.me" in href:
            num = re.sub(r"\D", "", href)
            if num:
                contact["whatsapp"] = f"+{num}"

    for elem in soup.find_all(["p", "div", "address"]):
        txt = elem.get_text(" ", strip=True)
        if any(kw in txt.lower() for kw in ["kondhwa", "budruk", "katraj", "pune", "maharashtra"]) and len(txt) < 250:
            contact["address"] = txt
            break

    data["contact_info"] = contact


def _extract_about_data(soup: BeautifulSoup, data: Dict[str, Any]):
    """Extract about overview and focus areas."""
    paragraphs = []
    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if len(txt) > 40:
            paragraphs.append(txt)
    data["overview"] = paragraphs[:5]
