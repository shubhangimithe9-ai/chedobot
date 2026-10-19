import sys
from pathlib import Path

# Ensure project root is in Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from chedobot import ChedoBot


def main():
    print("=" * 70)
    print("        CHEDO TECH CHATBOT (Jev/Laya + OKF + Gamma 2B)")
    print("=" * 70)
    print("Initializing Chedo Tech Chatbot...")

    try:
        bot = ChedoBot()
    except Exception as error:
        print(f"ERROR Initializing Chatbot: {error}")
        sys.exit(1)

    print("Chatbot is ready!")
    print("Type your question below.")
    print("Type 'exit' or 'quit' to terminate.\n")

    try:
        while True:
            try:
                query = input("User: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Chedo Tech Chatbot. Goodbye!")
                break

            if not query:
                continue

            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            answer, _ = bot.ask(query)
            print(f"\nChedoBot: {answer}\n")
    finally:
        bot.close()


if __name__ == "__main__":
    main()
