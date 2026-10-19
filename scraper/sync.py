import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from scraper.config import URL_REGISTRY, STATE_FILE
from scraper.extractor import fetch_page, extract_page_data
from scraper.md_generator import generate_okf_markdown
from scraper.validator import validate_markdown, backup_and_write


def load_state() -> Dict[str, Any]:
    """Load cached hashes from state.json."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Sync] Warning: Failed to read state file: {e}")
    return {}


def save_state(state: Dict[str, Any]):
    """Save updated hashes to state.json."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Sync] Warning: Failed to write state file: {e}")


def sync_knowledge(
    target_url: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Synchronize website pages with OKF markdown files.
    Only updates markdown files when changes are detected on the website (or force=True).
    """
    state = load_state()
    stats = {"scanned": 0, "updated": 0, "skipped": 0, "errors": 0}

    targets = URL_REGISTRY
    if target_url:
        if target_url in URL_REGISTRY:
            targets = {target_url: URL_REGISTRY[target_url]}
        else:
            print(f"[Sync] Error: URL '{target_url}' not found in scraper/config.py URL_REGISTRY.")
            return stats

    print("=" * 70)
    print("      CHEDO TECH WEBSITE -> OKF KNOWLEDGE BASE SYNC")
    print(f"      Mode: {'FORCE OVERWRITE' if force else 'SMART CHANGE DETECTION'}")
    print(f"      Dry Run: {dry_run}")
    print(f"      Targets to inspect: {len(targets)}")
    print("=" * 70)

    for url, cfg in targets.items():
        stats["scanned"] += 1
        target_file = Path(cfg["file"])
        category = cfg.get("category", "course")
        rel_path = str(target_file.relative_to(BASE_DIR)).replace("\\", "/")

        print(f"\n[{stats['scanned']}/{len(targets)}] Checking: {url}")
        print(f"  Target: {rel_path}")

        html = fetch_page(url)
        if not html:
            print(f"  [ERROR] Could not fetch webpage. Skipping.")
            stats["errors"] += 1
            continue

        extracted = extract_page_data(url, html, category=category)
        new_hash = extracted["content_hash"]
        old_hash = state.get(url, {}).get("content_hash")

        # Check if modified
        if not force and old_hash == new_hash and target_file.exists():
            print(f"  [UNCHANGED] No updates detected on website. Markdown is up to date.")
            stats["skipped"] += 1
            continue

        if old_hash and old_hash != new_hash:
            print(f"  [CHANGE DETECTED] Client updated website content!")
        elif force:
            print(f"  [FORCE] Rebuilding markdown from live website...")
        else:
            print(f"  [NEW / INITIAL SYNC] Building markdown from website...")

        # Generate OKF Markdown
        new_markdown = generate_okf_markdown(extracted, target_file, cfg)

        # Validate
        is_valid, reason = validate_markdown(new_markdown)
        if not is_valid:
            print(f"  [VALIDATION FAILED] {reason}. Skipping to protect existing knowledge.")
            stats["errors"] += 1
            continue

        if dry_run:
            print(f"  [DRY RUN] Validated successfully ({len(new_markdown)} chars). (Not writing to disk)")
            stats["updated"] += 1
            continue

        # Backup & Atomic Write
        success = backup_and_write(target_file, new_markdown)
        if success:
            state[url] = {
                "content_hash": new_hash,
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "file": rel_path,
                "title": cfg.get("title", "")
            }
            save_state(state)
            print(f"  [SUCCESS] Updated {rel_path}")
            stats["updated"] += 1
        else:
            print(f"  [ERROR] Failed to write {rel_path}")
            stats["errors"] += 1

    print("\n" + "=" * 70)
    print("SYNC SUMMARY:")
    print(f"  Total Scanned:  {stats['scanned']}")
    print(f"  Updated:        {stats['updated']}")
    print(f"  Unchanged:      {stats['skipped']}")
    print(f"  Errors:         {stats['errors']}")
    print("=" * 70)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Synchronize Chedo Tech website with OKF Knowledge Base.")
    parser.add_argument("--url", type=str, help="Sync a specific URL only.")
    parser.add_argument("--force", action="store_true", help="Force update all files even if unchanged.")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without saving to disk.")
    args = parser.parse_args()

    sync_knowledge(target_url=args.url, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
