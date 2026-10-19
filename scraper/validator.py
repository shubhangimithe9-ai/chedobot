import os
import shutil
import time
from pathlib import Path
from typing import Tuple

from okf.okf_query_engine import parse_frontmatter, extract_sections
from .config import BACKUP_DIR


def validate_markdown(content: str) -> Tuple[bool, str]:
    """
    Validate that the generated markdown is compatible with OKF Query Engine.
    Returns (is_valid, reason).
    """
    if not content or len(content.strip()) < 100:
        return False, "Content is empty or too short (< 100 chars)."

    try:
        metadata, body = parse_frontmatter(content)
    except Exception as e:
        return False, f"Failed to parse frontmatter: {e}"

    if not isinstance(metadata, dict):
        return False, "Metadata is not a valid YAML dictionary."

    for required_key in ["type", "title", "resource"]:
        if required_key not in metadata:
            return False, f"Missing required frontmatter key: {required_key}"

    if not body or len(body.strip()) < 50:
        return False, "Body content is empty or too short."

    try:
        sections = extract_sections(body)
        if not sections:
            return False, "No valid markdown sections (## headings) found."
    except Exception as e:
        return False, f"Failed to extract sections: {e}"

    return True, "Valid OKF Markdown"


def backup_and_write(target_file: Path, new_content: str) -> bool:
    """
    Safely backup the existing file, then atomically write the new content.
    """
    target_file = Path(target_file)
    target_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Backup existing file if it exists
    if target_file.exists():
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_subdir = BACKUP_DIR / timestamp
        backup_subdir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_subdir / target_file.name
        try:
            shutil.copy2(target_file, backup_path)
        except Exception as e:
            print(f"[Validator] Warning: Could not create backup: {e}")

    # 2. Atomic write using temporary file
    temp_file = target_file.with_suffix(".tmp")
    try:
        temp_file.write_text(new_content, encoding="utf-8")
        # Atomic replace
        if os.name == "nt" and target_file.exists():
            os.replace(temp_file, target_file)
        else:
            temp_file.replace(target_file)
        return True
    except Exception as e:
        print(f"[Validator] Error during atomic write to {target_file}: {e}")
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        return False
