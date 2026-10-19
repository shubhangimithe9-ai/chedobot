import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def generate_okf_markdown(
    extracted: Dict[str, Any],
    target_file: Path,
    config: Dict[str, Any]
) -> str:
    """
    Generate an OKF-compliant markdown string combining existing frontmatter/curated sections
    with newly scraped live website content.
    """
    existing_frontmatter = {}
    existing_text = ""

    if target_file.exists():
        try:
            existing_text = target_file.read_text(encoding="utf-8")
            if existing_text.startswith("---"):
                parts = existing_text.split("---", 2)
                if len(parts) >= 3:
                    existing_frontmatter = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            print(f"[Markdown Generator] Warning: Could not read existing frontmatter from {target_file}: {e}")

    # Build updated frontmatter
    fm = dict(existing_frontmatter)
    fm["type"] = config.get("type", fm.get("type", "Course"))
    fm["title"] = config.get("title", fm.get("title", extracted.get("title", "Course")))
    if extracted.get("description"):
        fm["description"] = extracted["description"]
    fm["resource"] = extracted["url"]

    # Ensure tags and sources exist
    if "tags" not in fm or not fm["tags"]:
        fm["tags"] = [fm["title"].lower().replace(" ", "-"), "chedo-tech", "programming"]
    if "sources" not in fm or not fm["sources"]:
        fm["sources"] = [{
            "id": f"{Path(target_file).stem}-page",
            "resource": extracted["url"],
            "title": f"Chedo Tech {fm['title']} official page"
        }]

    fm_yaml = yaml.dump(fm, sort_keys=False, default_flow_style=False, allow_unicode=True).strip()

    category = config.get("category", "course")
    if category == "contact":
        body = _build_contact_body(extracted, fm["title"])
    elif category == "about":
        body = _build_about_body(extracted, fm["title"])
    else:
        body = _build_course_body(extracted, fm["title"], existing_text)

    return f"---\n{fm_yaml}\n---\n\n{body}\n"


def _build_course_body(extracted: Dict[str, Any], title: str, existing_text: str) -> str:
    """Build markdown body for a course."""
    lines = [f"# {title}", ""]

    # 1. Course Overview
    lines.append("## Course Overview")
    lines.append("")
    overview = extracted.get("overview")
    if overview:
        for p in overview:
            lines.append(p)
            lines.append("")
    else:
        lines.append(f"{title} is an offline classroom course focused on practical programming and problem solving at Chedo Tech.")
        lines.append("")

    # 2. Course Format
    lines.append("## Course Format")
    lines.append("")
    lines.append("- Offline classroom learning")
    lines.append("- Pune center")
    lines.append("- Hands-on coding and mentor guidance")
    lines.append("- Technical interview preparation")
    lines.append("")

    # 3. Course Objective
    lines.append("## Course Objective")
    lines.append("")
    obj = extracted.get("format_details", {}).get("objective")
    if obj:
        lines.append(obj)
    else:
        lines.append(f"Develop strong real-world competence in {title} with comprehensive problem-solving skills.")
    lines.append("")

    # 4. Learning Path / Curriculum
    lines.append("## Learning Path")
    lines.append("")
    learning_path = extracted.get("learning_path", [])
    if learning_path:
        for idx, step in enumerate(learning_path, start=1):
            lines.append(f"{idx}. {step}")
    else:
        lines.append("1. Core Concepts & Foundations")
        lines.append("2. Logic Building & Syntax")
        lines.append("3. Practical Problem Solving")
        lines.append("4. Real-world Projects")
    lines.append("")

    # 5. Key Highlights & Mentor Notice
    lines.append("## Key Highlights")
    lines.append("")
    lines.append("- Direct mentorship under Chetan Dongarsane (Founder, Chedo Tech)")
    lines.append("- Structured offline classroom sessions in Pune")
    lines.append("- Hands-on milestone-based assignments")
    lines.append("- Official contact: +91 87931 00815")
    lines.append("")

    # 6. Frequently Asked Questions
    lines.append("## Frequently Asked Questions")
    lines.append("")
    lines.append("### Who is the mentor for this course?")
    lines.append("Chetan Dongarsane is the verified mentor and instructor at Chedo Tech.")
    lines.append("")
    lines.append("### Where are classes conducted?")
    lines.append("All training sessions are conducted in-person / offline at Chedo Tech, Pune.")
    lines.append("")
    lines.append("### What is the fee structure?")
    lines.append("Course fees vary per batch and track. Please contact Chedo Tech at +91 87931 00815 for official fee details.")
    lines.append("")

    # If any specific scraped FAQs exist, append them
    for faq in extracted.get("faqs", []):
        if faq.get("question") and faq.get("answer"):
            lines.append(f"### {faq['question']}")
            lines.append(faq["answer"])
            lines.append("")

    return "\n".join(lines).strip()


def _build_contact_body(extracted: Dict[str, Any], title: str) -> str:
    """Build markdown body for contact info."""
    c = extracted.get("contact_info", {})
    phone = c.get("phone", "+91 87931 00815")
    whatsapp = c.get("whatsapp", "+91 87931 00815")
    email = c.get("email", "chetan2469@gmail.com")
    location = c.get("address", "Pune, Maharashtra, India")
    website = c.get("website", "https://www.chedo.in/")

    return f"""# {title}

## Official Contact Information

- Phone: {phone}
- WhatsApp: {whatsapp}
- Email: {email}
- Website: {website}

## Official Communication Channels

Chedo Tech maintains these direct contact and support channels:

- Mobile & WhatsApp: {phone}
- Email Inquiries: {email}
- Official Website: {website}

## Location

{location}
Offline classroom training sessions and centers are located in Pune, Maharashtra.
"""


def _build_about_body(extracted: Dict[str, Any], title: str) -> str:
    """Build markdown body for about page."""
    overview = extracted.get("overview", [])
    overview_text = "\n\n".join(overview) if overview else (
        "Chedo Tech is a technology education and training institute founded by Chetan Dongarsane, "
        "focused on programming, software engineering, and industry-oriented technology learning."
    )

    return f"""# {title}

## Overview

{overview_text}

## Mentor & Leadership

- Founder & Lead Mentor: Chetan Dongarsane
- Educational Focus: Practical programming, DSA, Full-stack development, and Generative AI.
- Location: Pune, Maharashtra, India.
- Official Website: https://www.chedo.in/
"""
