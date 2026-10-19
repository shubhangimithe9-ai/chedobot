/**
 * Jev AI (@receptron/laya) Node.js Bridge for Chedo Tech Chatbot
 * 
 * Provides System-1 fast decision classification and query routing for ChedoBot.
 * Communicates via stdin/stdout JSON lines in persistent mode, or directly via CLI.
 */

import readline from "node:readline";
import path from "node:path";
import { Laya } from "@receptron/laya";

// Definition of System-1 Classification Schema
const CLASSIFICATION_SCHEMA = {
  intent: {
    type: "choice",
    instructions: "What is the user's primary intent regarding Chedo Tech?",
    criteria: {
      greeting: "Conversational greetings: hi, hello, hey, good morning, greetings",
      farewell: "Conversational closing or gratitude: goodbye, bye, thanks, thank you",
      course_list: "Asking for all courses, total count or number of courses, how many courses are offered, list of courses, or training options",
      course_detail: "Asking about a specific course curriculum, syllabus, topics, or technologies",
      mentors: "Asking who is the mentor, instructor, teacher, faculty, or who founded/leads Chedo Tech",
      fees: "Asking about course fees, cost, pricing, payment plans, or discounts",
      contact_info: "Asking for phone number, email, office address, location, or how to contact",
      about_chedotech: "Asking about Chedo Tech background, overview, mission, or institute details",
      learning_methodology: "Asking about teaching format, offline classroom, whiteboard coding, projects, or practice",
      faq: "General frequently asked questions about Chedo Tech training or certifications",
      unsupported: "Completely off-topic or unsupported topics (cooking, movies, weather, medicine, stocks, or courses Chedo does not teach)"
    }
  },
  is_supported: {
    type: "noul",
    instructions: "Is this query relevant to an educational technology academy, programming courses, admissions, fees, contact, or mentors?"
  },
  target_course: {
    type: "choice",
    instructions: "Which specific Chedo Tech course is the query referring to?",
    criteria: {
      none: "No specific course mentioned, or inquiry is general across all courses",
      "java-dsa": "Java + DSA (Core Java, Collections Framework, and Data Structures & Algorithms)",
      "python-dsa": "Python + DSA (Python with Data Structures & Algorithms)",
      "c-cpp-dsa": "C + C++ + DSA combined foundation and algorithms",
      "c-programming": "Core C Programming language",
      "cpp-programming": "C++ Programming course with OOP and STL",
      "java-programming": "Java Programming core fundamentals and OOP",
      "python-programming": "Python Programming language fundamentals",
      "dsa": "Dedicated Data Structures and Algorithms course",
      "mern-full-stack": "MERN Stack Web Development (MongoDB, Express, React, Node.js)",
      "java-full-stack": "Java Full Stack Development (Spring Boot, Angular/React, Databases)",
      "mobile-app-flutter": "Mobile Application Development with Flutter and Dart",
      "data-science-foundation": "Data Science Foundation (Python, Pandas, EDA, Statistics)",
      "data-science-ml-genai": "Data Science, Machine Learning, Deep Learning & Generative AI",
      "ui-ux-design": "UI/UX Design, user research, wireframing, and Figma prototyping",
      "kids-programming": "Programming for Kids / School students coding fundamentals"
    }
  },
  target_aspect: {
    type: "choice",
    instructions: "What specific aspect of the course or organization is requested?",
    criteria: {
      overview: "General overview, what the course is about, or general summary",
      syllabus: "Detailed syllabus, curriculum topics, phases, modules, or tools",
      mentor: "Mentor, instructor, faculty name, background, or teaching staff",
      fees: "Fee structure, tuition cost, pricing, or payment details",
      contact: "Phone number, email, address, or location details",
      eligibility: "Target audience, prerequisites, or who the course is for",
      format: "Course format, classroom setting, offline sessions, or whiteboard practice"
    }
  }
};

let layaInstance = null;

async function getLaya() {
  if (!layaInstance) {
    const t0 = Date.now();
    layaInstance = await Laya.load();
    const loadTime = Date.now() - t0;
    process.stderr.write(`[Laya Bridge] Model loaded in ${loadTime}ms from ${layaInstance.modelDir}\n`);
  }
  return layaInstance;
}

const VERIFIED_SUPPORTED_INTENTS = new Set([
  "course_list",
  "course_detail",
  "mentors",
  "fees",
  "contact_info",
  "about_chedotech",
  "learning_methodology"
]);

/**
 * Classify a user query using Laya System-1 forward pass.
 */
export async function classifyQuery(query) {
  const laya = await getLaya();
  const state = { query: query.trim() };

  const result = await laya.systemOne(state, CLASSIFICATION_SCHEMA);
  const answers = result.answers;

  const intent = answers.intent.choice;
  const intentConfidence = answers.intent.confidence;
  const isSupportedProb = answers.is_supported.noul;
  const targetCourse = answers.target_course.choice;
  const targetAspect = answers.target_aspect.choice;

  const isIntentSupported = VERIFIED_SUPPORTED_INTENTS.has(intent) || targetCourse !== "none";

  // Derive high-level routing decision
  let route = "okf_retrieve";
  if (intent === "greeting" || intent === "farewell") {
    route = "direct_conversational";
  } else if (intent === "unsupported") {
    route = "direct_unsupported";
  } else if (intent === "fees" || targetAspect === "fees") {
    route = "fees_guidance";
  } else if (intent === "mentors" || targetAspect === "mentor") {
    route = "mentor_inquiry";
  } else if (intent === "contact_info" || targetAspect === "contact") {
    route = "contact_inquiry";
  } else if (intent === "course_list") {
    route = "course_list";
  } else if (!isIntentSupported && isSupportedProb < 0.20) {
    route = "direct_unsupported";
  }

  const effectiveIsSupported = isIntentSupported || (isSupportedProb >= 0.20);

  return {
    query,
    intent,
    confidence: Number(intentConfidence.toFixed(4)),
    is_supported: effectiveIsSupported,
    support_score: Number(isSupportedProb.toFixed(4)),
    target_course: targetCourse,
    target_aspect: targetAspect,
    route,
    probabilities: {
      intent: answers.intent.probabilities,
      is_supported: isSupportedProb,
      target_course: answers.target_course.probabilities,
      target_aspect: answers.target_aspect.probabilities
    }
  };
}

/**
 * Run persistent line-by-line JSON-RPC loop over stdin/stdout.
 */
async function runIpcServer() {
  // Preload model
  await getLaya();
  process.stderr.write("[Laya Bridge] Ready for queries over stdin.\n");

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  for await (const line of rl) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    try {
      const req = JSON.parse(trimmed);

      if (req.cmd === "ping") {
        console.log(JSON.stringify({ id: req.id, status: "pong" }));
        continue;
      }

      if (req.cmd === "exit") {
        console.log(JSON.stringify({ id: req.id, status: "exiting" }));
        break;
      }

      const query = req.query || "";
      const classification = await classifyQuery(query);

      const response = {
        id: req.id,
        status: "ok",
        classification
      };

      console.log(JSON.stringify(response));
    } catch (err) {
      console.log(JSON.stringify({
        status: "error",
        error: String(err?.message || err)
      }));
    }
  }

  if (layaInstance) {
    await layaInstance.close();
  }
  process.exit(0);
}

// CLI / Standalone execution handler
async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--health")) {
    const laya = await getLaya();
    console.log(JSON.stringify({ status: "healthy", modelDir: laya.modelDir }));
    await laya.close();
    process.exit(0);
  }

  const queryIndex = args.indexOf("--query");
  if (queryIndex !== -1 && args[queryIndex + 1]) {
    const query = args[queryIndex + 1];
    const res = await classifyQuery(query);
    console.log(JSON.stringify(res, null, 2));
    if (layaInstance) await layaInstance.close();
    process.exit(0);
  }

  // Default: start persistent IPC server
  await runIpcServer();
}

main().catch((err) => {
  process.stderr.write(`[Laya Bridge Fatal Error] ${err.stack || err}\n`);
  process.exit(1);
});
