---
title: Chedo Tech AI Assistant
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# 🤖 Chedo Tech AI Assistant

Official Intelligent Assistant for Chedo Tech Courses & Enquiries.
Powered by a 3-Stage Pipeline: **Jev AI (@receptron/laya)** + **OKF Knowledge Base** + **Fine-Tuned Gamma 2B**.

---

## 🏛️ System Architecture

```text
       [ User Question ]
               │
               ▼
┌─────────────────────────────────┐
│     Stage 1: Jev AI / Laya      │
│     (@receptron/laya System-1)  │
│  • Intent Classification        │
│  • Course / Aspect Detection    │
│  • Out-of-Scope Hallucination   │
│    Guard (P(supported))         │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
[Direct Route]     [Targeted Query]
• Greeting/Bye            │
• Unsupported/Off-topic   ▼
                   ┌───────────────────────────────┐
                   │    Stage 2: OKF Engine        │
                   │ • 20 Verified Markdown Files  │
                   │ • Section & Semantic Scoring  │
                   │ • Anti-Hallucination Guard    │
                   └──────────────┬────────────────┘
                                  │ Grounded Context
                                  ▼
                   ┌───────────────────────────────┐
                   │   Stage 3: Gamma 2B GGUF      │
                   │ • llama-cpp-python            │
                   │ • Strict Fact Grounding       │
                   │ • Verified Response Output    │
                   └──────────────┬────────────────┘
                                  │
                                  ▼
                         [ ChedoBot Answer ]
```

---

## 🚀 Quick Start (Windows PowerShell)

### 1. Prerequisites
- **Node.js**: v20 or newer (`node --version`)
- **Python**: 3.10 or 3.11 (`python --version`)

### 2. Install Dependencies
```powershell
# 1. Install Node.js dependencies for Jev AI / Laya
npm install

# 2. Install Python dependencies
pip install -r requirements.txt
```

### 3. Run the Chatbot

**Interactive Web UI (Gradio):**
```powershell
python app.py
```
*Open http://localhost:8000 in your browser.*

**Interactive Terminal CLI:**
```powershell
python main.py
```

**Run Full Test Suite:**
```powershell
python test_chatbot.py
```

---

## 🎯 Verification Commands (PowerShell)

**Test Laya Node.js Bridge directly:**
```powershell
# Health check
node laya_bridge.mjs --health

# Test query classification
node laya_bridge.mjs --query "Who is the mentor for Python course?"
node laya_bridge.mjs --query "What is the fee for Java DSA?"
node laya_bridge.mjs --query "How do I make chocolate cake?"
```

---

## 🛡️ Anti-Hallucination Guardrails
- **Mentors**: Strictly enforces that Chetan Dongarsane is the verified mentor and founder at Chedo Tech.
- **Courses**: Strictly bounds answers to Chedo Tech's 15 verified courses.
- **Fees**: Course fees vary per batch; directs users to official contact (+91 87931 00815) instead of hallucinating arbitrary numbers.
- **Out-of-Scope**: Off-topic questions (cooking, health, stocks, etc.) are caught by Laya's support calibration and safely routed without hallucination.
