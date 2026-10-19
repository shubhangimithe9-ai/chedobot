import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

RESERVED_FILES = {
    "knowledge/index.md",
    "knowledge/courses/index.md",
    "knowledge/log.md",
}


COURSE_FILES = {
    "java-dsa.md",
    "python-dsa.md",
    "c-cpp-dsa.md",
    "c-programming.md",
    "cpp-programming.md",
    "java-programming.md",
    "python-programming.md",
    "dsa.md",
    "mern-full-stack.md",
    "java-full-stack.md",
    "mobile-app-flutter.md",
    "data-science-foundation.md",
    "data-science-ml-genai.md",
    "ui-ux-design.md",
    "kids-programming.md",
}


# ============================================================
# COURSE ALIASES
# ============================================================

COURSE_ALIASES = {
    "java-dsa.md": [
        "java + dsa",
        "java dsa",
        "java and dsa",
        "java with dsa",
        "java plus dsa",
    ],

    "python-dsa.md": [
        "python + dsa",
        "python dsa",
        "python and dsa",
        "python with dsa",
        "python plus dsa",
    ],

    "c-cpp-dsa.md": [
        "c + c++ + dsa",
        "c c++ dsa",
        "c/c++ dsa",
        "c cpp dsa",
        "c and c++ dsa",
    ],

    "c-programming.md": [
        "c programming",
        "c language",
        "c programming language",
    ],

    "cpp-programming.md": [
        "c++ programming",
        "cpp programming",
        "c plus plus programming",
        "c++ course",
        "cpp course",
    ],

    "java-programming.md": [
        "java programming",
        "java course",
        "core java",
        "core java programming",
    ],

    "python-programming.md": [
        "python programming",
        "python course",
        "core python",
    ],

    "dsa.md": [
        "data structures and algorithms",
        "data structures algorithms",
        "data structures & algorithms",
        "dsa",
    ],

    "mern-full-stack.md": [
        "mern",
        "mern stack",
        "mern full stack",
        "mern full stack development",
        "mern development",
    ],

    "java-full-stack.md": [
        "java full stack",
        "java full stack development",
        "java fullstack",
        "java fullstack development",
    ],

    "mobile-app-flutter.md": [
        "flutter",
        "flutter development",
        "mobile app development",
        "mobile app development flutter",
        "mobile application development",
    ],

    "data-science-foundation.md": [
        "data science foundation",
        "data science basics",
        "data science fundamentals",
    ],

    "data-science-ml-genai.md": [
        "data science machine learning generative ai",
        "data science ml genai",
        "data science machine learning",
        "machine learning generative ai",
        "generative ai",
        "genai",
    ],

    "ui-ux-design.md": [
        "ui ux",
        "ui/ux",
        "ui ux design",
        "ui/ux design",
        "ux design",
    ],

    "kids-programming.md": [
        "kids programming",
        "programming for kids",
        "kids coding",
        "coding for kids",
    ],
}


# ============================================================
# SECTION KEYWORDS
# ============================================================

SECTION_KEYWORDS = {
    "Technologies": [
        "technology",
        "technologies",
        "tech",
        "tech stack",
        "tools",
        "languages",
        "frameworks",
        "libraries",
    ],

    "Curriculum": [
        "curriculum",
        "syllabus",
        "topics",
        "modules",
        "subjects",
        "what will i learn",
        "what do i learn",
    ],

    "Course Format": [
        "format",
        "mode",
        "online",
        "offline",
        "classroom",
        "training mode",
        "course mode",
    ],

    "Who Is It For": [
        "who is it for",
        "who can join",
        "suitable for",
        "eligibility",
        "target audience",
        "beginners",
        "beginner",
    ],

    "Projects": [
        "projects",
        "project",
        "real world projects",
        "practical projects",
    ],

    "Objectives": [
        "objective",
        "objectives",
        "goal",
        "goals",
        "learning objectives",
    ],

    "Learning Path": [
        "learning path",
        "roadmap",
        "progression",
        "learning journey",
    ],

    "Overview": [
        "what is",
        "tell me about",
        "overview",
        "about this course",
        "course details",
    ],
}


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize(text):
    """
    Convert text into a simpler form for matching.
    """

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text):
    """
    Convert text into useful word tokens.
    """

    text = normalize(text)

    return set(
        re.findall(
            r"[a-zA-Z0-9+#/&.-]+",
            text
        )
    )


# ============================================================
# FRONTMATTER
# ============================================================

def parse_frontmatter(text):
    """
    Parse simple YAML-style frontmatter.

    Example:

    ---
    type: Course
    title: Java + DSA
    description: ...
    ---
    """

    metadata = {}
    text = text.lstrip()

    if not text.startswith("---"):
        return metadata, text

    parts = text.split("---", 2)

    if len(parts) < 3:
        return metadata, text

    raw_frontmatter = parts[1].strip()
    body = parts[2].strip()

    try:
        import yaml
        parsed = yaml.safe_load(raw_frontmatter)
        if isinstance(parsed, dict):
            return parsed, body
    except Exception:
        pass

    current_list = None

    for line in raw_frontmatter.splitlines():

        line = line.rstrip()

        if not line.strip():
            continue

        stripped = line.strip()

        if stripped.startswith("- "):

            if current_list:
                metadata[current_list].append(
                    stripped[2:].strip()
                )

            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)

        key = key.strip()
        value = value.strip()

        if value == "":
            metadata[key] = []
            current_list = key
            continue

        value = value.strip('"').strip("'")

        metadata[key] = value
        current_list = None

    return metadata, body


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(body):
    """
    Extract Markdown ## sections.

    Example:

    ## Technologies

    Java
    DSA

    becomes:

    {
        "title": "Technologies",
        "content": "Java\nDSA"
    }
    """

    sections = []

    matches = list(
        re.finditer(
            r"^##\s+(.+?)\s*$",
            body,
            re.MULTILINE
        )
    )

    for index, match in enumerate(matches):

        title = match.group(1).strip()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(body)

        content = body[start:end].strip()

        sections.append(
            {
                "title": title,
                "content": content,
            }
        )

    return sections


# ============================================================
# LOAD KNOWLEDGE
# ============================================================

def load_knowledge():

    records = []

    if not KNOWLEDGE_DIR.exists():
        print("ERROR: Knowledge directory not found:")
        print(KNOWLEDGE_DIR)
        return records

    for file_path in KNOWLEDGE_DIR.rglob("*.md"):

        relative_path = str(
            file_path.relative_to(BASE_DIR)
        ).replace("\\", "/")

        if relative_path in RESERVED_FILES:
            continue

        try:

            text = file_path.read_text(
                encoding="utf-8"
            )

            metadata, body = parse_frontmatter(text)

            sections = extract_sections(body)

            title = metadata.get(
                "title",
                file_path.stem.replace("-", " ").title()
            )

            description = metadata.get(
                "description",
                ""
            )

            record = {
                "file": relative_path,
                "path": str(file_path),
                "metadata": metadata,
                "body": body,
                "sections": sections,
                "title": title,
                "description": description,
                "type": metadata.get(
                    "type",
                    "Unknown"
                ),
            }

            records.append(record)

        except Exception as error:

            print(
                f"ERROR reading {relative_path}: {error}"
            )

    return records


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(query):

    q = normalize(query)

    # --------------------------------------------------------
    # COURSE-SPECIFIC QUERY HAS HIGHEST PRIORITY
    # --------------------------------------------------------
    # If the user explicitly mentions a course, treat the
    # question as a course query even when words like
    # "projects", "technologies", or "curriculum" are present.

    if detect_course(q):
        return "course"

    # --------------------------------------------------------
    # COURSE LIST
    # --------------------------------------------------------

    course_list_patterns = [
        r"\bwhat courses\b",
        r"\bwhich courses\b",
        r"\bcourses does chedo\b",
        r"\bcourses do chedo\b",
        r"\bcourse list\b",
        r"\blist.*courses\b",
        r"\bprograms does chedo\b",
        r"\bwhat programs\b",
        r"\bwhich programs\b",
        r"\bprogram list\b",
        r"\ball courses\b",
        r"\ball programs\b",
        r"\btotal courses\b",
        r"\bhow many courses\b",
        r"\bhow many total courses\b",
        r"\bnumber of courses\b",
        r"\btotal number of courses\b",
        r"\bcourse count\b",
        r"\bcount.*courses\b",
        r"\bcourses info\b",
        r"\bcourses information\b",
        r"\bcourses offered\b",
        r"\bavailable courses\b",
        r"\bcourses provided\b",
        r"\bprovide.*courses\b",
        r"\boffer.*courses\b",
    ]

    for pattern in course_list_patterns:

        if re.search(pattern, q):
            return "course_list"

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    contact_patterns = [
        "contact",
        "contact number",
        "contact no",
        "phone number",
        "mobile number",
        "telephone",
        "email address",
        "office address",
        "address",
        "reach chedo",
    ]

    if any(
        phrase in q
        for phrase in contact_patterns
    ):
        return "contact"

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    about_patterns = [
        "who is chedo",
        "what is chedo",
        "about chedo",
        "about chedo tech",
        "tell me about chedo",
        "tell me about chedo tech",
    ]

    if any(
        phrase in q
        for phrase in about_patterns
    ):
        return "about"

    # --------------------------------------------------------
    # LEARNING
    # --------------------------------------------------------

    learning_patterns = [
        "how does chedo teach",
        "how does chedo train",
        "learning approach",
        "teaching approach",
        "learning methodology",
        "how do students learn",
        "how is training done",
    ]

    if any(
        phrase in q
        for phrase in learning_patterns
    ):
        return "learning"

    # --------------------------------------------------------
    # PROJECTS
    # --------------------------------------------------------

    project_patterns = [
        "projects",
        "project based",
        "real world project",
        "practical project",
        "what projects",
    ]

    if any(
        phrase in q
        for phrase in project_patterns
    ):
        return "projects"

    # --------------------------------------------------------
    # FAQ
    # --------------------------------------------------------

    faq_patterns = [
        "faq",
        "frequently asked",
        "common question",
        "do you provide",
        "is there",
        "can i join",
    ]

    if any(
        phrase in q
        for phrase in faq_patterns
    ):
        return "faq"

    # --------------------------------------------------------
    # COURSE KEYWORDS
    # --------------------------------------------------------

    course_keywords = [
        "java",
        "python",
        "c programming",
        "c++",
        "dsa",
        "data structures",
        "algorithms",
        "mern",
        "full stack",
        "flutter",
        "mobile app",
        "data science",
        "machine learning",
        "generative ai",
        "genai",
        "ui ux",
        "ui/ux",
        "kids programming",
    ]

    if any(
        keyword in q
        for keyword in course_keywords
    ):
        return "course"

    return "general"

# ============================================================
# EXACT COURSE DETECTION
# ============================================================

def detect_course(query):

    q = normalize(query)

    matches = []

    for filename, aliases in COURSE_ALIASES.items():

        for alias in aliases:

            alias_normalized = normalize(alias)

            if alias_normalized in q:

                matches.append(
                    (
                        len(alias_normalized),
                        filename
                    )
                )

    if not matches:
        return None

    # Longest matching alias wins.
    matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return matches[0][1]


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section(query):

    q = normalize(query)

    best_section = None
    best_length = 0

    for section_name, keywords in SECTION_KEYWORDS.items():

        for keyword in keywords:

            keyword_normalized = normalize(keyword)

            if keyword_normalized in q:

                if len(keyword_normalized) > best_length:

                    best_length = len(
                        keyword_normalized
                    )

                    best_section = section_name

    return best_section


# ============================================================
# SECTION FINDING
# ============================================================

def find_matching_section(
    record,
    requested_section
):

    if not requested_section:
        return None

    requested_normalized = normalize(
        requested_section
    )

    for section in record["sections"]:

        section_title = normalize(
            section["title"]
        )

        # Exact title match
        if (
            requested_normalized
            == section_title
        ):
            return section

        # Partial match
        if (
            requested_normalized in section_title
            or section_title in requested_normalized
        ):
            return section

    return None


# ============================================================
# SPECIAL RETRIEVAL
# ============================================================

def retrieve_special(
    records,
    record_type
):

    return [
        record
        for record in records
        if record["type"].lower()
        == record_type.lower()
    ]


# ============================================================
# GENERAL RELEVANCE SCORE
# ============================================================

def relevance_score(
    query,
    record
):

    q_tokens = tokenize(query)

    title_tokens = tokenize(
        record["title"]
    )

    description_tokens = tokenize(
        record["description"]
    )

    body_tokens = tokenize(
        record["body"]
    )

    score = 0

    # Title match
    score += len(
        q_tokens.intersection(
            title_tokens
        )
    ) * 20

    # Description match
    score += len(
        q_tokens.intersection(
            description_tokens
        )
    ) * 8

    # Body match
    score += len(
        q_tokens.intersection(
            body_tokens
        )
    ) * 2

    return score


# ============================================================
# RETRIEVE KNOWLEDGE
# ============================================================

def retrieve_knowledge(
    query,
    records,
    top_k=5
):

    intent = detect_intent(query)

    # --------------------------------------------------------
    # COURSE LIST
    # --------------------------------------------------------

    if intent == "course_list":

        course_records = [
            record
            for record in records
            if record["file"].split("/")[-1]
            in COURSE_FILES
        ]

        course_records.sort(
            key=lambda record:
            record["title"].lower()
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": course_records,
        }

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if intent == "contact":

        results = retrieve_special(
            records,
            "ContactInformation"
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": results,
        }

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    if intent == "about":

        results = retrieve_special(
            records,
            "Organization"
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": results,
        }

    # --------------------------------------------------------
    # LEARNING
    # --------------------------------------------------------

    if intent == "learning":

        results = retrieve_special(
            records,
            "Learning"
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": results,
        }

    # --------------------------------------------------------
    # PROJECTS
    # --------------------------------------------------------

    if intent == "projects":

        results = retrieve_special(
            records,
            "Projects"
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": results,
        }

    # --------------------------------------------------------
    # FAQ
    # --------------------------------------------------------

    if intent == "faq":

        results = retrieve_special(
            records,
            "FAQ"
        )

        return {
            "intent": intent,
            "course": None,
            "section": None,
            "records": results,
        }

    # --------------------------------------------------------
    # COURSE-SPECIFIC QUERY
    # --------------------------------------------------------

    if intent == "course":

        course_file = detect_course(query)

        requested_section = detect_section(query)

        # Exact course found
        if course_file:

            exact_records = [
                record
                for record in records
                if record["file"].split("/")[-1]
                == course_file
            ]

            if exact_records:

                record = exact_records[0]

                matched_section = find_matching_section(
                    record,
                    requested_section
                )

                result_record = dict(record)

                result_record[
                    "matched_section"
                ] = matched_section

                return {
                    "intent": intent,
                    "course": record["title"],
                    "section": (
                        matched_section["title"]
                        if matched_section
                        else None
                    ),
                    "records": [
                        result_record
                    ],
                }

        # No exact course found.
        # Fall back to relevance scoring.

    # --------------------------------------------------------
    # GENERAL / FALLBACK SEARCH
    # --------------------------------------------------------

    scored = []

    for record in records:

        score = relevance_score(
            query,
            record
        )

        if score > 0:

            scored.append(
                (
                    score,
                    record
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    results = []

    for score, record in scored[:top_k]:

        result_record = dict(record)

        result_record["score"] = score

        results.append(
            result_record
        )

    return {
        "intent": intent,
        "course": None,
        "section": None,
        "records": results,
    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(
    query,
    result
):

    print()
    print("=" * 70)

    print(
        f"Query: {query}"
    )

    print(
        f"Intent: {result['intent']}"
    )

    if result.get("course"):

        print(
            f"Course: {result['course']}"
        )

    if result.get("section"):

        print(
            f"Section: {result['section']}"
        )

    records = result["records"]

    print(
        f"Retrieved records: {len(records)}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # COURSE LIST
    # --------------------------------------------------------

    if result["intent"] == "course_list":

        print()
        print("CHEDO TECH COURSES")
        print("-" * 60)

        for index, record in enumerate(
            records,
            start=1
        ):

            print(
                f"{index:02d}. {record['title']}"
            )

        print()

        return

    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not records:

        print()
        print(
            "No matching knowledge found."
        )
        print()

        return

    # --------------------------------------------------------
    # DISPLAY RECORDS
    # --------------------------------------------------------

    for index, record in enumerate(
        records,
        start=1
    ):

        print()
        print(
            f"Result {index}:"
        )

        print(
            f"Title: {record['title']}"
        )

        print(
            f"Type: {record['type']}"
        )

        print(
            f"File: {record['file']}"
        )

        if "score" in record:

            print(
                f"Score: {record['score']}"
            )

        # ----------------------------------------------------
        # SECTION RESULT
        # ----------------------------------------------------

        matched_section = record.get(
            "matched_section"
        )

        if matched_section:

            print()
            print(
                f"## {matched_section['title']}"
            )

            print(
                matched_section["content"]
            )

        else:

            print()

            if record["description"]:

                print(
                    "Description:"
                )

                print(
                    record["description"]
                )

            print()

            print(
                record["body"]
            )

    print()


# ============================================================
# COMMAND HELP
# ============================================================

def print_help():

    print()
    print("Available commands:")
    print()
    print("/files  - Show loaded knowledge files")
    print("/count  - Show number of knowledge files")
    print("/intent - Test intent detection")
    print("/help   - Show this help")
    print("exit    - Exit chatbot")
    print()


# ============================================================
# SHOW FILES
# ============================================================

def show_files(records):

    print()
    print("LOADED KNOWLEDGE FILES")
    print("-" * 60)

    for index, record in enumerate(
        records,
        start=1
    ):

        print(
            f"{index:02d}. "
            f"{record['file']}"
        )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("CHEDO TECH OKF QUERY ENGINE")
    print("=" * 70)

    print()
    print(
        f"Knowledge directory: {KNOWLEDGE_DIR}"
    )

    records = load_knowledge()

    print(
        f"Knowledge files loaded: {len(records)}"
    )

    print()

    if not records:

        print(
            "ERROR: No knowledge files found."
        )

        return

    print(
        "Type your question."
    )

    print(
        "Type '/help' for commands."
    )

    print(
        "Type 'exit' to stop."
    )

    print()

    while True:

        try:

            query = input("Query: ").strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            print("Exiting...")
            break

        if not query:
            continue

        if query.lower() == "exit":

            print("Goodbye!")
            break

        # ----------------------------------------------------
        # COMMANDS
        # ----------------------------------------------------

        if query.lower() == "/help":

            print_help()
            continue

        if query.lower() == "/files":

            show_files(records)
            continue

        if query.lower() == "/count":

            print()
            print(
                f"Knowledge files: {len(records)}"
            )
            print()

            continue

        if query.lower() == "/intent":

            test_query = input(
                "Enter query for intent test: "
            ).strip()

            print()

            print(
                "Intent:",
                detect_intent(test_query)
            )

            print(
                "Course:",
                detect_course(test_query)
            )

            print(
                "Section:",
                detect_section(test_query)
            )

            print()

            continue

        # ----------------------------------------------------
        # NORMAL QUERY
        # ----------------------------------------------------

        result = retrieve_knowledge(
            query,
            records
        )

        display_result(
            query,
            result
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()