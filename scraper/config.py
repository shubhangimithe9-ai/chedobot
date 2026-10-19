from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "okf" / "knowledge"
STATE_FILE = Path(__file__).resolve().parent / "state.json"
BACKUP_DIR = BASE_DIR / "backup" / "knowledge_backups"

# Scraper HTTP Settings
REQUEST_TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ChedoSyncBot/1.0"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Registry of URL -> Markdown File Mappings
URL_REGISTRY = {
    "https://chedo.in/about.php": {
        "file": KNOWLEDGE_DIR / "about" / "index.md",
        "type": "Organization",
        "title": "About Chedo Tech",
        "category": "about",
    },
    "https://chedo.in/contact.php": {
        "file": KNOWLEDGE_DIR / "contact" / "index.md",
        "type": "ContactInformation",
        "title": "Chedo Tech Contact Information",
        "category": "contact",
    },
    "https://chedo.in/courses/python-dsa.php": {
        "file": KNOWLEDGE_DIR / "courses" / "python-dsa.md",
        "type": "Course",
        "title": "Python + DSA",
        "category": "course",
    },
    "https://chedo.in/courses/java-dsa.php": {
        "file": KNOWLEDGE_DIR / "courses" / "java-dsa.md",
        "type": "Course",
        "title": "Java + DSA",
        "category": "course",
    },
    "https://chedo.in/courses/c-cpp-dsa.php": {
        "file": KNOWLEDGE_DIR / "courses" / "c-cpp-dsa.md",
        "type": "Course",
        "title": "C + C++ + DSA",
        "category": "course",
    },
    "https://chedo.in/courses/c-programming.php": {
        "file": KNOWLEDGE_DIR / "courses" / "c-programming.md",
        "type": "Course",
        "title": "C Programming",
        "category": "course",
    },
    "https://chedo.in/courses/cpp-programming.php": {
        "file": KNOWLEDGE_DIR / "courses" / "cpp-programming.md",
        "type": "Course",
        "title": "C++ Programming",
        "category": "course",
    },
    "https://chedo.in/courses/java-programming.php": {
        "file": KNOWLEDGE_DIR / "courses" / "java-programming.md",
        "type": "Course",
        "title": "Java Programming",
        "category": "course",
    },
    "https://chedo.in/courses/python-programming.php": {
        "file": KNOWLEDGE_DIR / "courses" / "python-programming.md",
        "type": "Course",
        "title": "Python Programming",
        "category": "course",
    },
    "https://chedo.in/courses/data-structures-algorithms.php": {
        "file": KNOWLEDGE_DIR / "courses" / "dsa.md",
        "type": "Course",
        "title": "Data Structures & Algorithms",
        "category": "course",
    },
    "https://chedo.in/courses/mern-full-stack.php": {
        "file": KNOWLEDGE_DIR / "courses" / "mern-full-stack.md",
        "type": "Course",
        "title": "MERN Full Stack Development",
        "category": "course",
    },
    "https://chedo.in/courses/java-full-stack.php": {
        "file": KNOWLEDGE_DIR / "courses" / "java-full-stack.md",
        "type": "Course",
        "title": "Java Full Stack Development",
        "category": "course",
    },
    "https://chedo.in/courses/mobile-app-development.php": {
        "file": KNOWLEDGE_DIR / "courses" / "mobile-app-flutter.md",
        "type": "Course",
        "title": "Mobile App Development (Flutter)",
        "category": "course",
    },
    "https://chedo.in/courses/data-science-foundation.php": {
        "file": KNOWLEDGE_DIR / "courses" / "data-science-foundation.md",
        "type": "Course",
        "title": "Data Science Foundation",
        "category": "course",
    },
    "https://chedo.in/courses/data-science.php": {
        "file": KNOWLEDGE_DIR / "courses" / "data-science-ml-genai.md",
        "type": "Course",
        "title": "Data Science, Machine Learning & Generative AI",
        "category": "course",
    },
    "https://chedo.in/courses/ui-ux-design.php": {
        "file": KNOWLEDGE_DIR / "courses" / "ui-ux-design.md",
        "type": "Course",
        "title": "UI/UX Design",
        "category": "course",
    },
    "https://chedo.in/courses/kids-programming.php": {
        "file": KNOWLEDGE_DIR / "courses" / "kids-programming.md",
        "type": "Course",
        "title": "Kids Programming",
        "category": "course",
    },
}
