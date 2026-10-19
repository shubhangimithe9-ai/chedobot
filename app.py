import sys
from pathlib import Path
import gradio as gr

# Ensure project root is in Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from chedobot import ChedoBot

print("Initializing Chedo Tech Chatbot...")
bot = ChedoBot()


def user_submit(user_message, history):
    if not user_message or not user_message.strip():
        yield "", history or []
        return

    history = history or []
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": "Thinking... 💭"})
    yield "", history

    for partial_answer in bot.stream_ask(user_message):
        history[-1]["content"] = partial_answer
        yield "", history


def clear_chat():
    return []


# Custom CSS for modern visual design
custom_css = """
.header-container {
    text-align: center;
    padding: 28px 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
    border-radius: 16px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.3);
}
.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #ffffff, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header-subtitle {
    font-size: 1.05rem;
    color: #c7d2fe;
    opacity: 0.95;
    margin-bottom: 14px;
}
.badge-container {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(8px);
    padding: 4px 14px;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #e0e7ff;
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.main-container {
    max-width: 950px;
    margin: 0 auto;
}
.footer-text {
    text-align: center;
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 16px;
}
"""

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

with gr.Blocks(title="Chedo Tech AI Assistant") as demo:
    with gr.Column(elem_classes=["main-container"]):
        gr.HTML("""
            <div class="header-container">
                <div class="header-title">🤖 Chedo Tech AI Assistant</div>
                <div class="header-subtitle">Official Intelligent Assistant for Chedo Tech Courses & Enquiries</div>
                <div class="badge-container">
                    <span class="status-badge">🟢 Online</span>
                    <span class="status-badge">🎯 Jev AI (Laya) Router</span>
                    <span class="status-badge">⚡ OKF Grounded</span>
                    <span class="status-badge">🧠 Fine-Tuned Gamma 2B</span>
                </div>
            </div>
        """)

        chatbot = gr.Chatbot(
            height=500,
            label="Conversation"
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Ask anything about Chedo Tech courses, admissions, mentors, or contact details...",
                label="Your Question",
                scale=5,
                container=False,
                autofocus=True
            )
            submit_btn = gr.Button("Send 🚀", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm")

        with gr.Accordion("⚙️ Live Website Sync & Knowledge Base Management", open=False):
            with gr.Row():
                sync_status = gr.Textbox(
                    label="Sync Status",
                    value="Knowledge Base is connected with live chedo.in pages.",
                    interactive=False,
                    scale=4
                )
                sync_btn = gr.Button("🔄 Sync Website Now", variant="secondary", scale=1)

            def handle_sync():
                from scraper.sync import sync_knowledge
                stats = sync_knowledge(force=False)
                reloaded = bot.reload_knowledge()
                return f"✅ Synced: {stats['scanned']} scanned ({stats['updated']} updated, {stats['skipped']} unchanged, {stats['errors']} errors). In-memory knowledge reloaded ({reloaded} records)."

            sync_btn.click(handle_sync, outputs=[sync_status])

        gr.Examples(
            examples=[
                "What is Chedo Tech?",
                "What courses does Chedo Tech offer?",
                "Tell me about the Java + DSA course",
                "What is the contact number of Chedo Tech?",
                "Who is the mentor for Python course?"
            ],
            inputs=msg,
            label="💡 Suggested Questions"
        )

        gr.HTML("""
            <div class="footer-text">
                © Chedo Tech • Powered by Jev AI (@receptron/laya) • OKF Architecture • Fine-Tuned Gamma 2B
            </div>
        """)

    submit_btn.click(user_submit, inputs=[msg, chatbot], outputs=[msg, chatbot])
    msg.submit(user_submit, inputs=[msg, chatbot], outputs=[msg, chatbot])
    clear_btn.click(clear_chat, outputs=[chatbot])


import os
import socket


def is_port_free(port: int, host: str = "0.0.0.0") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def get_available_port(preferred_port: int = 8000, host: str = "0.0.0.0") -> int:
    candidate_ports = [preferred_port, 7860, 8080, 8001, 8002, 7861]
    seen = set()
    candidates = [p for p in candidate_ports if not (p in seen or seen.add(p))]

    for port in candidates:
        if is_port_free(port, host):
            return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


if __name__ == "__main__":
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    env_port = os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT")
    requested_port = int(env_port) if env_port else 8000

    target_port = get_available_port(requested_port, server_name)
    if target_port != requested_port:
        print(f"⚠️ Port {requested_port} is in use. Automatically falling back to available port {target_port}...")

    print(f"Launching Chedo Tech AI Assistant Gradio UI on http://localhost:{target_port} ({server_name}:{target_port})...")
    demo.launch(server_name=server_name, server_port=target_port, share=False, theme=theme, css=custom_css)
