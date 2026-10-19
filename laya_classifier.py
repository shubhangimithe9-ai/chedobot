import os
import sys
import json
import time
import atexit
import logging
import threading
import subprocess
from pathlib import Path

logger = logging.getLogger("LayaClassifier")

BASE_DIR = Path(__file__).resolve().parent
BRIDGE_SCRIPT = BASE_DIR / "laya_bridge.mjs"

# Known Chedo Tech courses mapped to OKF markdown filenames
COURSE_KEY_MAP = {
    "java-dsa": "java-dsa.md",
    "python-dsa": "python-dsa.md",
    "c-cpp-dsa": "c-cpp-dsa.md",
    "c-programming": "c-programming.md",
    "cpp-programming": "cpp-programming.md",
    "java-programming": "java-programming.md",
    "python-programming": "python-programming.md",
    "dsa": "dsa.md",
    "mern-full-stack": "mern-full-stack.md",
    "java-full-stack": "java-full-stack.md",
    "mobile-app-flutter": "mobile-app-flutter.md",
    "data-science-foundation": "data-science-foundation.md",
    "data-science-ml-genai": "data-science-ml-genai.md",
    "ui-ux-design": "ui-ux-design.md",
    "kids-programming": "kids-programming.md",
}

GREETINGS = {"hi", "hello", "hey", "hallo", "greetings", "good morning", "good afternoon", "good evening", "hi there", "hello there"}
FAREWELLS = {"thanks", "thank you", "thankyou", "thanks a lot", "many thanks", "bye", "goodbye", "see you", "exit", "quit"}


class LayaClassifier:
    """
    Python client for Jev AI (@receptron/laya) System-1 Decision Model.
    Communicates with a persistent Node.js bridge process over JSON lines.
    Includes automatic recovery and graceful fallback if Node or Laya fails.
    """

    def __init__(self, bridge_path=None, node_cmd="node", timeout=20.0, enabled=True):
        self.bridge_path = Path(bridge_path) if bridge_path else BRIDGE_SCRIPT
        self.node_cmd = node_cmd
        self.timeout = timeout
        self.enabled = enabled
        self.process = None
        self._lock = threading.Lock()
        self._req_id = 0
        self.is_ready = False

        if self.enabled:
            self._start_bridge()

        atexit.register(self.close)

    def _start_bridge(self):
        """Starts the persistent Node.js Laya bridge process."""
        if not self.bridge_path.exists():
            print(f"[LayaClassifier] Warning: Bridge script not found at {self.bridge_path}. Using fallback.")
            return

        try:
            cmd = [self.node_cmd, str(self.bridge_path)]
            print("[LayaClassifier] Starting Jev AI (@receptron/laya) bridge process...")
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                cwd=str(BASE_DIR)
            )

            # Background thread to drain stderr to prevent pipe buffer deadlocks
            def _drain_stderr():
                try:
                    for line in iter(self.process.stderr.readline, ""):
                        if line.strip():
                            logger.debug(f"[LayaBridge] {line.strip()}")
                except Exception:
                    pass

            stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
            stderr_thread.start()

            # Wait for ready signal from stderr or ping
            time.sleep(0.5)
            if self.process.poll() is not None:
                print("[LayaClassifier] Bridge exited prematurely. Using fallback.")
                self.process = None
                return

            self.is_ready = True
            print("[LayaClassifier] Jev AI bridge process connected successfully.")
        except Exception as e:
            print(f"[LayaClassifier] Error starting Node.js bridge: {e}. Falling back to rule-based routing.")
            self.process = None

    def _send_request(self, payload):
        """Sends a JSON request to the bridge and reads the JSON response."""
        if not self.process or self.process.poll() is not None:
            self._start_bridge()
            if not self.process:
                return None

        self._req_id += 1
        payload["id"] = self._req_id
        line = json.dumps(payload) + "\n"

        try:
            self.process.stdin.write(line)
            self.process.stdin.flush()

            # Read single response line
            resp_line = self.process.stdout.readline()
            if not resp_line:
                print("[LayaClassifier] Empty response received from bridge.")
                return None

            return json.loads(resp_line.strip())
        except Exception as e:
            print(f"[LayaClassifier] Bridge communication error: {e}")
            return None

    def classify(self, query):
        """
        Classifies a user query using Laya System-1 decision model.
        Falls back safely to local heuristics if Laya is unavailable.
        """
        query_clean = query.strip()
        if not query_clean:
            return self._fallback_classify(query_clean)

        if not self.enabled or not self.process:
            return self._fallback_classify(query_clean)

        with self._lock:
            try:
                resp = self._send_request({"cmd": "classify", "query": query_clean})
                if resp and resp.get("status") == "ok" and "classification" in resp:
                    cls = resp["classification"]
                    cls["source"] = "jev_laya"
                    # Attach mapped okf course filename if recognized
                    target_course = cls.get("target_course")
                    cls["course_file"] = COURSE_KEY_MAP.get(target_course)
                    return cls
            except Exception as e:
                print(f"[LayaClassifier] Error during classification: {e}. Using fallback.")

        return self._fallback_classify(query_clean)

    def _fallback_classify(self, query):
        """
        Safe local heuristic classification when Laya is not active.
        Ensures ChedoBot remains 100% operational in any circumstance.
        """
        q_norm = query.strip().lower().rstrip("?!.")
        
        # Greetings
        if q_norm in GREETINGS:
            return {
                "query": query,
                "intent": "greeting",
                "confidence": 0.99,
                "is_supported": True,
                "support_score": 0.95,
                "target_course": "none",
                "target_aspect": "overview",
                "route": "direct_conversational",
                "source": "fallback_rules",
                "course_file": None
            }

        # Farewells
        if q_norm in FAREWELLS:
            return {
                "query": query,
                "intent": "farewell",
                "confidence": 0.99,
                "is_supported": True,
                "support_score": 0.95,
                "target_course": "none",
                "target_aspect": "overview",
                "route": "direct_conversational",
                "source": "fallback_rules",
                "course_file": None
            }

        # Detect courses
        target_course = "none"
        course_file = None
        if "java" in q_norm and "dsa" in q_norm:
            target_course = "java-dsa"
        elif "python" in q_norm and "dsa" in q_norm:
            target_course = "python-dsa"
        elif "c++" in q_norm or "cpp" in q_norm:
            target_course = "cpp-programming"
        elif "c programming" in q_norm or "c language" in q_norm:
            target_course = "c-programming"
        elif "java full stack" in q_norm:
            target_course = "java-full-stack"
        elif "mern" in q_norm:
            target_course = "mern-full-stack"
        elif "flutter" in q_norm:
            target_course = "mobile-app-flutter"
        elif "data science" in q_norm:
            target_course = "data-science-foundation"
        elif "ui" in q_norm or "ux" in q_norm:
            target_course = "ui-ux-design"
        elif "kid" in q_norm:
            target_course = "kids-programming"
        elif "python" in q_norm:
            target_course = "python-programming"
        elif "java" in q_norm:
            target_course = "java-programming"
        elif "dsa" in q_norm:
            target_course = "dsa"

        if target_course in COURSE_KEY_MAP:
            course_file = COURSE_KEY_MAP[target_course]

        # Detect aspects
        target_aspect = "overview"
        if any(w in q_norm for w in ["mentor", "who teaches", "instructor", "faculty", "trainer", "chetan"]):
            target_aspect = "mentor"
        elif any(w in q_norm for w in ["fee", "fees", "cost", "price", "pricing", "charge"]):
            target_aspect = "fees"
        elif any(w in q_norm for w in ["contact", "phone", "number", "email", "address", "call"]):
            target_aspect = "contact"
        elif any(w in q_norm for w in ["syllabus", "curriculum", "topics", "content"]):
            target_aspect = "syllabus"

        # Detect intent and route
        intent = "course_detail"
        route = "okf_retrieve"

        if target_aspect == "mentor":
            intent = "mentors"
            route = "mentor_inquiry"
        elif target_aspect == "fees":
            intent = "fees"
            route = "fees_guidance"
        elif target_aspect == "contact":
            intent = "contact_info"
            route = "contact_inquiry"
        elif any(w in q_norm for w in [
            "what courses", "courses offer", "all courses", "list of courses", "available courses",
            "total courses", "how many courses", "number of courses", "course count", "courses info",
            "courses provided", "what programs", "which courses"
        ]):
            intent = "course_list"
            route = "course_list"
        elif "about" in q_norm or ("chedo" in q_norm and "what is" in q_norm):
            intent = "about_chedotech"
            route = "okf_retrieve"

        # Check if the query is relevant to Chedo Tech or educational courses
        is_relevant = (
            target_course != "none"
            or target_aspect in ["mentor", "fees", "contact"]
            or intent in ["mentors", "fees", "contact_info", "course_list", "about_chedotech"]
            or any(kw in q_norm for kw in [
                "chedo", "course", "training", "program", "class", "admission", "enroll", "batch",
                "study", "learn", "syllabus", "mentor", "fees", "tuition", "institute", "academy", "tech",
                "curriculum", "placement", "job", "certificate", "offline", "online", "java", "python",
                "c++", "cpp", "flutter", "data science", "mern", "ui", "ux", "dsa"
            ])
        )

        if not is_relevant:
            return {
                "query": query,
                "intent": "unsupported",
                "confidence": 0.90,
                "is_supported": False,
                "support_score": 0.05,
                "target_course": "none",
                "target_aspect": "overview",
                "route": "direct_unsupported",
                "source": "fallback_rules",
                "course_file": None
            }

        return {
            "query": query,
            "intent": intent,
            "confidence": 0.85,
            "is_supported": True,
            "support_score": 0.85,
            "target_course": target_course,
            "target_aspect": target_aspect,
            "route": route,
            "source": "fallback_rules",
            "course_file": course_file
        }

    def close(self):
        """Closes the Node.js bridge process cleanly."""
        with self._lock:
            if self.process:
                try:
                    self.process.stdin.write(json.dumps({"cmd": "exit"}) + "\n")
                    self.process.stdin.flush()
                    self.process.wait(timeout=2.0)
                except Exception:
                    try:
                        self.process.terminate()
                    except Exception:
                        pass
                self.process = None
                self.is_ready = False
