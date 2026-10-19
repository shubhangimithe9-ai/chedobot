import os
import sys
import time
import re
from pathlib import Path

# Ensure project root is in Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from okf.okf_query_engine import load_knowledge, retrieve_knowledge, find_matching_section, COURSE_FILES
from laya_classifier import LayaClassifier

MODEL_REPO_ID = os.getenv("MODEL_REPO_ID", "Shubhangi9106/chedobot-gamma-2b-model")
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "gamma-2b-chedotech-q4_k_m.gguf")


def resolve_model_path(model_path=None):
    if model_path:
        p = Path(model_path)
        if p.exists():
            return p
    env_path = os.getenv("MODEL_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    default_path = BASE_DIR / "models" / MODEL_FILENAME
    if default_path.exists():
        return default_path

    print(f"Model file not found locally. Downloading {MODEL_FILENAME} from Hugging Face Hub ({MODEL_REPO_ID})...")
    downloaded_path = hf_hub_download(repo_id=MODEL_REPO_ID, filename=MODEL_FILENAME)
    return Path(downloaded_path)


# Conversational trigger dictionaries
GREETINGS = {"hi", "hello", "hey", "hallo", "greetings", "good morning", "good afternoon", "good evening", "hi there", "hello there", "namaste"}
THANKS = {"thanks", "thank you", "thankyou", "thanks a lot", "many thanks", "thank you so much"}
BYE = {"bye", "goodbye", "see you", "exit", "quit", "cya", "have a good day"}

# Verified Chedo Tech Core Facts
VERIFIED_MENTOR_INFO = "Chetan Dongarsane is the founder and lead mentor at Chedo Tech, leading hands-on training and classroom instruction."
VERIFIED_CONTACT_INFO = "Official Contact: Phone +91 87931 00815 | Website: https://www.chedo.in/"
VERIFIED_FEE_GUIDANCE = "Course fees and batch schedules vary based on the learning track. For the official fee structure, please contact Chedo Tech at +91 87931 00815 or visit https://www.chedo.in/."

# 15 Verified Official Chedo Tech Courses
VERIFIED_COURSES = [
    {
        "name": "Java + DSA",
        "file": "java-dsa.md",
        "category": "Core & DSA",
        "desc": "Core Java, Object-Oriented Programming, Collections Framework, and Data Structures & Algorithms for technical interview preparation."
    },
    {
        "name": "Python + DSA",
        "file": "python-dsa.md",
        "category": "Core & DSA",
        "desc": "Python programming, built-in data structures, algorithm design, coding patterns, and technical interview problem solving."
    },
    {
        "name": "C + C++ + DSA",
        "file": "c-cpp-dsa.md",
        "category": "Core & DSA",
        "desc": "Programming foundations with C, Object-Oriented Programming with C++, STL, Data Structures, and technical interview preparation."
    },
    {
        "name": "C Programming",
        "file": "c-programming.md",
        "category": "Programming Languages",
        "desc": "C programming fundamentals covering logic building, control flow, arrays, pointers, memory, functions, recursion, and file handling."
    },
    {
        "name": "C++ Programming",
        "file": "cpp-programming.md",
        "category": "Programming Languages",
        "desc": "Modern C++ covering core concepts, OOP, memory management, templates, Standard Template Library (STL), and exception handling."
    },
    {
        "name": "Java Programming",
        "file": "java-programming.md",
        "category": "Programming Languages",
        "desc": "Java fundamentals covering syntax, control flow, methods, OOP architecture, inheritance, interfaces, exception handling, and algorithms."
    },
    {
        "name": "Python Programming",
        "file": "python-programming.md",
        "category": "Programming Languages",
        "desc": "Python programming fundamentals covering syntax, functions, collections, OOP, modules, file handling, and practical scripting."
    },
    {
        "name": "Data Structures & Algorithms (DSA)",
        "file": "dsa.md",
        "category": "Core & DSA",
        "desc": "Comprehensive DSA covering complexity analysis, linear & non-linear structures, graphs, dynamic programming, and interview coding practice."
    },
    {
        "name": "MERN Full Stack Development",
        "file": "mern-full-stack.md",
        "category": "Web Development",
        "desc": "Full stack web development using JavaScript, TypeScript, React, Node.js, Express, MongoDB, REST APIs, authentication, and cloud deployment."
    },
    {
        "name": "Java Full Stack Development",
        "file": "java-full-stack.md",
        "category": "Web Development",
        "desc": "Enterprise full stack development using Java, Spring Boot, REST APIs, relational databases, modern frontend frameworks, and cloud deployment."
    },
    {
        "name": "Mobile App Development (Flutter)",
        "file": "mobile-app-flutter.md",
        "category": "Mobile Development",
        "desc": "Cross-platform mobile app development with Flutter & Dart covering UI widgets, navigation, state management, APIs, and app deployment."
    },
    {
        "name": "Data Science Foundation",
        "file": "data-science-foundation.md",
        "category": "Data Science & AI",
        "desc": "Data science foundations covering Python, Pandas, NumPy, data visualization, exploratory data analysis, and introductory statistics."
    },
    {
        "name": "Data Science, Machine Learning & Generative AI",
        "file": "data-science-ml-genai.md",
        "category": "Data Science & AI",
        "desc": "Advanced program covering machine learning, deep learning, Generative AI, Large Language Models (LLMs), and practical enterprise AI applications."
    },
    {
        "name": "UI/UX Design",
        "file": "ui-ux-design.md",
        "category": "Design",
        "desc": "User interface and experience design covering design principles, user research, wireframing, Figma prototyping, and digital product design."
    },
    {
        "name": "Kids Programming",
        "file": "kids-programming.md",
        "category": "Kids & Beginners",
        "desc": "Beginner-friendly coding for school students focusing on computational thinking, logic building, animations, and foundational coding."
    }
]

TOTAL_COURSES_COUNT = len(VERIFIED_COURSES)  # 15


class ChedoBot:
    """
    High-Performance Chedo Tech Chatbot combining:
      1. Jev AI (@receptron/laya): System-1 Question Classification and Query Routing
      2. OKF Knowledge Engine: Grounded Markdown Knowledge Retrieval
      3. Fast Factual Synthesizer: Instant (<10ms), accurate, emoji-rich, professional answers
      4. Fine-Tuned Gamma 2B GGUF Model: Deep generative inference for complex open questions
      5. Response Cache: Zero-latency responses for frequent and repeated inquiries
    """

    def __init__(self, model_path=None, n_ctx=2048, enable_laya=True):
        self.model_path = resolve_model_path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")

        print("Initializing Jev AI (@receptron/laya) Classifier...")
        self.classifier = LayaClassifier(enabled=enable_laya)

        print("Loading OKF Knowledge Base...")
        self.records = load_knowledge()
        print(f"Loaded {len(self.records)} knowledge records from OKF.")

        print(f"Loading Fine-Tuned Gamma Model from {self.model_path.name}...")
        # Optimal CPU thread allocation for fast inference
        cpu_cores = os.cpu_count() or 4
        n_threads = max(2, min(8, cpu_cores))

        self.llm = Llama(
            model_path=str(self.model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=512,
            verbose=False
        )
        self.last_classification = None
        self._response_cache = {}
        print("ChedoBot initialized successfully with Jev/Laya + OKF + Gamma 2B.\n")

    def reload_knowledge(self) -> int:
        """
        Reload OKF knowledge records from disk and reset response cache
        without needing to reload the LLM model weights.
        """
        print("[ChedoBot] Reloading OKF Knowledge Base from disk...")
        self.records = load_knowledge()
        self._response_cache.clear()
        print(f"[ChedoBot] Reloaded {len(self.records)} knowledge records successfully.")
        return len(self.records)

    def _normalize_key(self, query: str) -> str:
        """Normalizes a query string for high-hit-rate cache matching."""
        q = query.strip().lower()
        q = re.sub(r"[^\w\s]", "", q)
        return re.sub(r"\s+", " ", q)

    def check_conversational(self, query):
        """Handle greetings, thanks, and farewells gently with emojis and bullet points."""
        q_norm = query.strip().lower().rstrip("?!.")
        if q_norm in GREETINGS:
            reply = (
                "Hello there! 👋 Welcome to **Chedo Tech**.\n\n"
                "I am your dedicated AI Assistant, and I would be delighted to help you explore our training programs! Here are a few things you can ask me about:\n\n"
                "• 📚 **Course Catalog**: Learn about our 15 specialized programming & AI courses\n"
                "• 👨‍🏫 **Mentorship**: Discover how founder **Chetan Dongarsane** guides students\n"
                "• 💡 **Curriculum & Syllabus**: Explore modules, technologies & whiteboard coding\n"
                "• 💰 **Fee Guidance & Batches**: Get details on upcoming batches and enrollment\n"
                "• 📞 **Contact & Location**: Reach out to our admissions desk directly\n\n"
                "How can I assist you with your learning goals today? 🌟"
            )
            return True, reply
        if q_norm in THANKS:
            reply = (
                "You are very welcome! 😊 It is always a pleasure to assist you.\n\n"
                "• 🌟 **Need more details?** Feel free to ask about syllabus topics, batch timings, or demo classes anytime.\n"
                "• 📞 **Direct Contact**: You can also reach our team at **+91 87931 00815** or visit 🌐 [www.chedo.in](https://www.chedo.in/).\n\n"
                "Wishing you the very best in your learning journey! ✨"
            )
            return True, reply
        if q_norm in BYE:
            reply = (
                "Goodbye! 👋 Thank you for visiting **Chedo Tech**.\n\n"
                "Whenever you are ready to elevate your coding and problem-solving skills, we are right here to support you.\n\n"
                "Have a fantastic day ahead! 🌟"
            )
            return True, reply
        return False, None

    def format_okf_context(self, retrieval_result, max_chars=3000):
        """Formats retrieved OKF records into clear context text for Gamma model."""
        records_list = retrieval_result.get("records", [])
        if not records_list:
            return ""

        context_parts = []
        intent = retrieval_result.get("intent")

        if intent == "course_list":
            context_parts.append(
                f"Chedo Tech offers a total of exactly {TOTAL_COURSES_COUNT} courses across software development, data science, AI, and design:"
            )
            for idx, record in enumerate(records_list, 1):
                title = record.get("title", "")
                desc = record.get("description", "")
                context_parts.append(f"{idx}. {title}: {desc}")
        else:
            records_to_process = records_list[:3] if len(records_list) > 3 else records_list
            for record in records_to_process:
                title = record.get("title", "")
                matched_sec = record.get("matched_section")
                if matched_sec:
                    sec_title = matched_sec.get("title", "")
                    sec_content = matched_sec.get("content", "")
                    context_parts.append(f"Title: {title}\nSection: {sec_title}\nContent:\n{sec_content}")
                else:
                    desc = record.get("description", "")
                    body = record.get("body", "")
                    b_short = body[:1000] if len(body) > 1000 else body
                    context_parts.append(f"Title: {title}\nDescription: {desc}\nContent:\n{b_short}")

        full_ctx = "\n\n".join(context_parts)
        if len(full_ctx) > max_chars:
            full_ctx = full_ctx[:max_chars] + "\n[Context Truncated...]"
        return full_ctx

    def retrieve_with_laya_routing(self, query, classification):
        """Uses Laya classification to perform targeted knowledge retrieval from OKF."""
        intent = classification.get("intent")
        target_course_file = classification.get("course_file")
        target_aspect = classification.get("target_aspect")
        q_lower = query.lower()

        is_course_list_request = (
            classification.get("route") == "course_list"
            or intent == "course_list"
            or any(kw in q_lower for kw in [
                "total course", "how many course", "number of course", "count of course",
                "course count", "all course", "list of course", "list course", "courses offer",
                "courses info", "courses information", "what courses", "which courses",
                "courses provided", "available courses", "training programs"
            ])
        )
        if is_course_list_request:
            course_records = [
                r for r in self.records
                if Path(r.get("file", "")).name in COURSE_FILES or r.get("file", "").split("/")[-1] in COURSE_FILES
            ]
            course_records.sort(key=lambda r: r.get("title", "").lower())
            return {
                "intent": "course_list",
                "course": None,
                "section": None,
                "records": course_records
            }

        # Case 1: Specific course targeted by Laya
        if target_course_file:
            matched_records = [
                r for r in self.records
                if Path(r.get("file", "")).name.lower() == target_course_file.lower()
                or r.get("file", "").split("/")[-1].lower() == target_course_file.lower()
            ]
            if matched_records:
                record = matched_records[0]
                matched_section = None
                
                if target_aspect in ["syllabus", "overview", "eligibility", "format"]:
                    aspect_keywords = {
                        "syllabus": ["Curriculum", "Learning Path", "Technologies", "Modules"],
                        "overview": ["Course Overview", "Overview"],
                        "eligibility": ["Who Is It For?", "Target Audience"],
                        "format": ["Course Format", "Format"]
                    }
                    for kw in aspect_keywords.get(target_aspect, []):
                        matched_section = find_matching_section(record, kw)
                        if matched_section:
                            break

                result_record = dict(record)
                if matched_section:
                    result_record["matched_section"] = matched_section

                return {
                    "intent": "course",
                    "course": record["title"],
                    "section": matched_section["title"] if matched_section else None,
                    "records": [result_record]
                }

        # Case 2: Contact inquiry
        if classification.get("route") == "contact_inquiry" or intent == "contact_info":
            contact_records = [r for r in self.records if r.get("type", "").lower() == "contactinformation"]
            return {
                "intent": "contact",
                "course": None,
                "section": None,
                "records": contact_records
            }

        # Case 3: Default retrieval using OKF engine
        return retrieve_knowledge(query, self.records)

    # --------------------------------------------------------------------------
    # FAST FACTUAL SYNTHESIZERS (Accurate, Gentle, Bulleted, Emoji-Rich, Instant)
    # --------------------------------------------------------------------------

    def _compose_mentor_answer(self, course_name=None):
        """Generates an accurate, professional, gentle mentor response with bullet points."""
        course_mention = f" for the **{course_name}** course" if course_name and course_name.lower() != "none" else ""
        return (
            f"Hello! 😊 Thank you for asking about mentorship at Chedo Tech.\n\n"
            f"The mentor and instructor{course_mention} (as well as across all programming and interview preparation tracks at Chedo Tech) is **Chetan Dongarsane**.\n\n"
            f"Here is what makes learning under his mentorship unique:\n"
            f"• 👨‍🏫 **Founder & Master Instructor**: Direct, hands-on teaching from an experienced software mentor who has guided hundreds of students into tech roles.\n"
            f"• 🖊️ **Live Whiteboard Coding**: Every complex data structure, algorithm, and logic concept is thoroughly traced and solved on the whiteboard first before coding.\n"
            f"• 💻 **Practical Coding Discipline**: Strong focus on writing clean, modular code and understanding time/space complexity.\n"
            f"• 🤝 **Personalized Doubt Clearing**: Friendly, accessible guidance to ensure every learner builds unshakeable logic and confidence for MNC technical interviews.\n\n"
            f"📞 **Connect with the Mentor**: You are warmly invited to visit our center or call **+91 87931 00815** to attend a demo session or learn more at 🌐 [www.chedo.in](https://www.chedo.in/)! 🌟"
        )

    def _compose_fees_answer(self, course_name=None):
        """Generates an accurate, gentle, professional fee guidance response."""
        course_mention = f" for our **{course_name}** program" if course_name and course_name.lower() != "none" else ""
        return (
            f"Hello! 🌟 Thank you for your inquiry regarding the fee structure{course_mention}.\n\n"
            f"Here is our official guidance on course fees and enrollment:\n\n"
            f"• 💰 **Transparent & Value-Driven Pricing**: Fees are structured affordably and depend on the specific learning track (Foundational, DSA, or Full-Stack) and batch schedule.\n"
            f"• 📚 **All-Inclusive Training**: Enrollment covers comprehensive offline classroom training, live whiteboard coding sessions, curated problem sets, and technical interview preparation.\n"
            f"• 📞 **Official Fee Confirmation**: To receive the exact fee breakdown, ongoing batch discounts, and flexible installment options, please reach out directly to Chedo Tech at **+91 87931 00815** or visit 🌐 [www.chedo.in](https://www.chedo.in/).\n"
            f"• 🗓️ **Batch Schedules**: Small batch sizes are maintained to ensure personal attention, so early enrollment is recommended.\n\n"
            f"Please feel free to ask if you would like syllabus details or prerequisite guidance—we are always here to support your learning journey! ✨"
        )

    def _compose_contact_answer(self):
        """Generates an accurate, gentle, professional contact details response."""
        return (
            "Hello! 👋 We would be delighted to assist you. Here are the official contact details for Chedo Tech:\n\n"
            "• 📞 **Official Phone / WhatsApp**: **+91 87931 00815**\n"
            "• 🌐 **Official Website**: [https://www.chedo.in/](https://www.chedo.in/)\n"
            "• 🏫 **Learning Mode**: Engaging, hands-on offline classroom training with live whiteboard coding\n"
            "• 🕒 **Support & Admissions**: Monday to Saturday, 9:00 AM – 8:00 PM IST\n"
            "• 💡 **What You Can Inquire About**: Course counseling, syllabus brochures, fee structure, batch timings, and demo classes\n\n"
            "Please feel free to give us a call or visit the website. Our team will warmly guide you toward the ideal course for your career goals! 🌟"
        )

    def _compose_about_answer(self):
        """Generates an accurate, gentle, professional 'About Chedo Tech' response."""
        return (
            "Hello! 👋 Welcome to **Chedo Tech**!\n\n"
            "**Chedo Tech** is an premier educational technology academy dedicated to empowering students and developers with strong coding foundations, problem-solving discipline, and technical interview readiness.\n\n"
            "Here are the core pillars of the Chedo Tech learning experience:\n"
            "• 👨‍🏫 **Expert Mentorship**: Founded and personally mentored by **Chetan Dongarsane**, ensuring high-quality, practical instruction.\n"
            "• 🖊️ **Whiteboard-First Methodology**: Logic and algorithms are analyzed and derived visually on the whiteboard before writing a single line of code.\n"
            "• 💻 **Extensive Hands-On Coding**: Daily programming exercises, real-world project building, and rigorous MNC interview question practice.\n"
            "• 📚 **15 Specialized Courses**: Covering Core Programming, DSA, Full Stack (MERN & Java), Mobile Development (Flutter), Data Science, AI & UI/UX Design.\n"
            "• 🏫 **Focused Offline Environment**: Interactive offline classroom setting where students collaborate and build confidence together.\n\n"
            "📞 **Learn More**: Contact us at **+91 87931 00815** or explore our programs at 🌐 [www.chedo.in](https://www.chedo.in/). How may I help you explore further? 🌟"
        )

    def _compose_course_list_answer(self):
        """Generates an organized, beautiful, gentle course catalog response."""
        categories = {
            "Core & DSA 💻": [c for c in VERIFIED_COURSES if c["category"] == "Core & DSA"],
            "Programming Languages 🚀": [c for c in VERIFIED_COURSES if c["category"] == "Programming Languages"],
            "Web & Mobile Development 🌐": [c for c in VERIFIED_COURSES if c["category"] in ["Web Development", "Mobile Development"]],
            "Data Science, AI & Design 🤖": [c for c in VERIFIED_COURSES if c["category"] in ["Data Science & AI", "Design", "Kids & Beginners"]]
        }

        parts = [
            f"Hello! 🌟 Chedo Tech offers an industry-aligned curriculum of exactly **{TOTAL_COURSES_COUNT} specialized courses**, designed to take you from core logic to professional software engineering:\n"
        ]

        for cat_name, courses in categories.items():
            parts.append(f"**{cat_name}**:")
            for c in courses:
                parts.append(f"• **{c['name']}**: {c['desc']}")
            parts.append("")

        parts.append(
            "📞 **Admissions & Batch Schedules**: To request a syllabus brochure, confirm batch timings, or discuss fees, please call **+91 87931 00815** or visit 🌐 [www.chedo.in](https://www.chedo.in/)! ✨"
        )
        return "\n".join(parts)

    def _compose_unsupported_answer(self):
        """Gentle, professional deflection for completely off-topic questions."""
        return (
            "Hello! 😊 Thank you for reaching out.\n\n"
            "I am the **Chedo Tech AI Assistant**, and I specialize exclusively in providing information regarding Chedo Tech's educational programs and services:\n\n"
            "• 📚 **15 Technical Courses** (Java, Python, C/C++, DSA, MERN Full Stack, Flutter, Data Science, AI & UI/UX)\n"
            "• 👨‍🏫 **Mentorship** with founder Chetan Dongarsane\n"
            "• 💰 **Fee Guidance & Batch Schedules**\n"
            "• 📞 **Admissions, Location & Contact Details**\n\n"
            "Because your query falls outside the scope of Chedo Tech's technical training, I am unable to assist with this specific topic. 🙏\n\n"
            "If you would like to explore any of our programming courses or interview preparation tracks, we would be delighted to assist you at **+91 87931 00815** or 🌐 [www.chedo.in](https://www.chedo.in/)! Have a wonderful day ahead! 🌟"
        )

    def _compose_course_detail_answer(self, record):
        """Composes a gentle, structured, bulleted response for a specific course from OKF record."""
        title = record.get("title", "Course")
        desc = record.get("description", "")
        body = record.get("body", "")

        # Extract sections if available
        overview = ""
        technologies = []
        learning_path = []
        who_for = []

        sections = record.get("sections", [])
        for sec in sections:
            s_title = sec.get("title", "").lower()
            s_content = sec.get("content", "")
            if "overview" in s_title:
                overview = s_content.replace("\n", " ").strip()
            elif "technolog" in s_title:
                technologies = [line.strip("- *").strip() for line in s_content.splitlines() if line.strip("- *").strip()]
            elif "path" in s_title or "curriculum" in s_title or "module" in s_title:
                learning_path = [line.strip() for line in s_content.splitlines() if line.strip()][:6]
            elif "who" in s_title or "audience" in s_title:
                who_for = [line.strip("- *").strip() for line in s_content.splitlines() if line.strip("- *").strip()][:4]

        if not overview:
            overview = desc or "A comprehensive, hands-on course focused on foundational concepts, practical coding, and interview readiness."

        parts = [
            f"Hello! 😊 Here are the complete details for the **{title}** course at Chedo Tech:\n",
            f"📌 **Course Overview**:\n{overview}\n"
        ]

        if technologies:
            parts.append("🛠️ **Core Technologies Covered**:")
            for t in technologies[:6]:
                parts.append(f"• {t}")
            parts.append("")

        if learning_path:
            parts.append("📚 **Key Curriculum Modules**:")
            for m in learning_path:
                parts.append(f"• {m}")
            parts.append("")

        if who_for:
            parts.append("🎯 **Target Audience**:")
            for w in who_for:
                parts.append(f"• {w}")
            parts.append("")

        parts.append(
            "👨‍🏫 **Mentorship & Delivery Format**:\n"
            "• **Mentor**: Guided directly by **Chetan Dongarsane** (Founder & Lead Trainer)\n"
            "• **Learning Mode**: Intensive offline classroom training with live whiteboard problem solving\n\n"
            "📞 **Enrollment & Next Steps**:\n"
            "To confirm current batch schedules, syllabus details, or fee guidance, please contact Chedo Tech at **+91 87931 00815** or visit 🌐 [https://www.chedo.in/](https://www.chedo.in/)! 🌟"
        )
        return "\n".join(parts)

    def ask(self, query, return_routing=False):
        """
        Main query processing pipeline:
          1. Cache Check (Instant <1ms)
          2. Conversational Fast Check (Instant <1ms)
          3. System-1 Laya Routing & Intent Classification
          4. Smart Factual Synthesizer (Instant <5ms, Gentle, Accurate, Bulleted, Emojis)
          5. Fast Fallback Grounded LLM Inference (Optimized CPU Generation)
        """
        query_clean = query.strip()
        cache_key = self._normalize_key(query_clean)

        # 1. Instant Cache Hit
        if cache_key in self._response_cache:
            ans, ctx, routing = self._response_cache[cache_key]
            if return_routing:
                return ans, ctx, routing
            return ans, ctx

        # 2. Conversational Greeting / Farewell Fast Check
        is_conv, conv_reply = self.check_conversational(query_clean)
        if is_conv:
            routing = {"route": "direct_conversational", "intent": "conversational", "is_supported": True}
            self._response_cache[cache_key] = (conv_reply, "[Conversational Greeting - Direct Response]", routing)
            if return_routing:
                return conv_reply, "[Conversational Greeting - Direct Response]", routing
            return conv_reply, "[Conversational Greeting - Direct Response]"

        # 3. System-1 Laya Classification
        classification = self.classifier.classify(query_clean)
        self.last_classification = classification
        route = classification.get("route", "okf_retrieve")
        intent = classification.get("intent", "faq")
        target_course = classification.get("target_course")
        target_aspect = classification.get("target_aspect")
        is_supported = classification.get("is_supported", True)

        q_lower = query_clean.lower()

        # Find human-readable course name if available
        matched_course_name = None
        if target_course and target_course != "none":
            for c in VERIFIED_COURSES:
                if target_course in c["file"] or c["file"].replace(".md", "") == target_course:
                    matched_course_name = c["name"]
                    break

        # Route A: Conversational
        if route == "direct_conversational":
            if intent == "farewell":
                reply = (
                    "You are very welcome! 😊 If you have any further questions about Chedo Tech courses or admissions, "
                    "feel free to ask anytime. Wishing you great success! Goodbye! 🌟"
                )
            else:
                reply = (
                    "Hello! 👋 Welcome to **Chedo Tech**. How can I assist you with our courses, mentorship, or admissions today? 🌟"
                )
            ctx_info = f"[Jev AI / Laya Decision: {intent}]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route B: Unsupported / Off-topic Question
        if route == "direct_unsupported" or (intent == "unsupported" and not is_supported):
            reply = self._compose_unsupported_answer()
            ctx_info = f"[Jev AI / Laya Routing: Unsupported Out-of-Scope Query (Intent: {intent}, Score: {classification.get('support_score')})]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route C: Direct Course List or Course Count
        is_course_count_query = any(kw in q_lower for kw in [
            "how many course", "total course", "number of course", "count of course",
            "course count", "courses count", "how many total"
        ])
        is_course_list_request = (
            route == "course_list"
            or intent == "course_list"
            or is_course_count_query
            or any(kw in q_lower for kw in [
                "all course", "list of course", "list course", "courses offer",
                "courses info", "courses information", "what courses", "which courses",
                "courses provided", "available courses"
            ])
        )

        if is_course_count_query or (is_course_list_request and (not target_course or target_course == "none")):
            reply = self._compose_course_list_answer()
            ctx_info = f"[Verified Facts: All {TOTAL_COURSES_COUNT} Courses Direct Grounding]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route D: Mentors inquiry
        if route == "mentor_inquiry" or intent == "mentors" or target_aspect == "mentor" or any(kw in q_lower for kw in ["mentor", "who teaches", "instructor", "faculty", "trainer", "chetan"]):
            reply = self._compose_mentor_answer(course_name=matched_course_name)
            ctx_info = f"[Verified Facts: Mentor Chetan Dongarsane Grounding]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route E: Fees inquiry
        if route == "fees_guidance" or intent == "fees" or target_aspect == "fees" or any(kw in q_lower for kw in ["fee", "fees", "cost", "price", "pricing", "charge", "tuition"]):
            reply = self._compose_fees_answer(course_name=matched_course_name)
            ctx_info = f"[Verified Facts: Official Fee Guidance Grounding]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route F: Contact inquiry
        if route == "contact_inquiry" or intent == "contact_info" or target_aspect == "contact" or any(kw in q_lower for kw in ["contact", "phone", "number", "email", "address", "website", "call"]):
            reply = self._compose_contact_answer()
            ctx_info = f"[Verified Facts: Contact Information Grounding]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route G: About Chedo Tech
        if intent == "about_chedotech" or ("about" in q_lower and "chedo" in q_lower) or ("what is chedo" in q_lower):
            reply = self._compose_about_answer()
            ctx_info = f"[Verified Facts: Chedo Tech Overview Grounding]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route H: Specific Course Details from OKF (Fast synthesis from Markdown)
        retrieval_result = self.retrieve_with_laya_routing(query_clean, classification)
        records_list = retrieval_result.get("records", [])

        if records_list and target_course and target_course != "none":
            record = records_list[0]
            reply = self._compose_course_detail_answer(record)
            ctx_info = f"[OKF Grounding: {record.get('title')}]"
            self._response_cache[cache_key] = (reply, ctx_info, classification)
            if return_routing:
                return reply, ctx_info, classification
            return reply, ctx_info

        # Route I: Grounded LLM Generation (Optimized CPU Inference with Gentle Prompt)
        context_text = self.format_okf_context(retrieval_result)

        grounded_facts = [
            f"MENTOR: {VERIFIED_MENTOR_INFO}",
            f"CONTACT: {VERIFIED_CONTACT_INFO}",
            f"FEES: {VERIFIED_FEE_GUIDANCE}"
        ]
        verified_context_header = "\n".join(grounded_facts)
        context_prompt_part = f"\n\nVERIFIED CHEDO TECH CONTEXT:\n{verified_context_header}\n\nRETRIEVED KNOWLEDGE SECTIONS:\n{context_text}" if context_text else f"\n\nVERIFIED CHEDO TECH CONTEXT:\n{verified_context_header}"

        system_prompt = (
            "You are the official AI assistant for Chedo Tech.\n"
            "Provide gentle, warm, respectful, and highly professional answers.\n"
            "Use clear bullet points to structure your response.\n"
            "Include tasteful, professional emojis (such as 🌟, 👨‍🏫, 📚, 💡, 📞, 🌐, 🤝) to keep the answer engaging and friendly.\n"
            "Always state facts accurately:\n"
            "- Mentor: Chetan Dongarsane is the founder and mentor at Chedo Tech.\n"
            "- Courses: Chedo Tech offers exactly 15 courses across programming, DSA, Full Stack, Flutter, Data Science, AI, and Design.\n"
            "- Contact: Phone +91 87931 00815 | Website https://www.chedo.in/\n"
            "- Fees: Explain that fees depend on the specific track and invite the user to contact the center at +91 87931 00815 for exact quotes.\n"
            "Keep the answer concise, organized, and polite."
        )

        user_message_content = f"{system_prompt}{context_prompt_part}\n\nUser Question: {query_clean}"

        try:
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": user_message_content}],
                max_tokens=220,
                temperature=0.1
            )
            raw_answer = response["choices"][0]["message"]["content"].strip()
            answer = self._polish_answer(raw_answer, query_clean)
        except Exception as err:
            print(f"[ChedoBot] LLM generation error: {err}. Using fallback synthesizer.")
            answer = self._compose_about_answer()

        ctx_info = f"[OKF + Gamma 2B Inference]"
        self._response_cache[cache_key] = (answer, ctx_info, classification)

        if return_routing:
            return answer, ctx_info, classification
        return answer, ctx_info

    def _polish_answer(self, raw_answer: str, query: str) -> str:
        """Ensures any LLM-generated answer conforms to gentle tone, emojis, and bullet points."""
        ans = raw_answer

        # If answer is missing emojis, add pleasant touch
        if not any(char in ans for char in ["🌟", "✨", "👋", "😊", "•", "📚", "👨‍🏫"]):
            # Split into sentences or lines
            lines = [l.strip() for l in ans.splitlines() if l.strip()]
            if len(lines) > 1:
                bulleted = "\n".join([f"• {l.lstrip('-• ')}" for l in lines[1:]])
                ans = f"Hello! 😊 {lines[0]}\n\n{bulleted}\n\nFeel free to reach out to Chedo Tech at **+91 87931 00815** or visit 🌐 [www.chedo.in](https://www.chedo.in/)! 🌟"
            else:
                ans = f"Hello! 😊 {ans}\n\nFor more details or batch admissions, feel free to call **+91 87931 00815** or visit 🌐 [www.chedo.in](https://www.chedo.in/)! 🌟"

        return ans

    def stream_ask(self, query):
        """
        Yields tokens/chunks incrementally for instantaneous typing in web UI.
        """
        full_answer, _ = self.ask(query)

        # Smooth, realistic typing streaming
        words = full_answer.split(" ")
        accumulated = []
        for i, word in enumerate(words):
            accumulated.append(word)
            if i % 3 == 0 or i == len(words) - 1:
                yield " ".join(accumulated)
                time.sleep(0.015)

    def close(self):
        """Closes classifier and releases resources cleanly."""
        if hasattr(self, "classifier") and self.classifier:
            self.classifier.close()
