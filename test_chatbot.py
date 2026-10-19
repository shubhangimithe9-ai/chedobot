import sys
from pathlib import Path

# Ensure project root is in Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from chedobot import ChedoBot


def run_tests():
    print("=" * 70)
    print("      CHEDO TECH CHATBOT TEST SUITE (Jev/Laya + OKF + Gamma 2B)")
    print("=" * 70)
    
    bot = ChedoBot()

    test_queries = [
        "What is Chedo Tech?",
        "What courses does Chedo Tech offer?",
        "Who is the mentor for Python course?",
        "What is the fee structure for Java DSA course?",
        "What is the official contact number and website of Chedo Tech?",
        "How do I bake a chocolate cake at home?"
    ]

    for index, query in enumerate(test_queries, start=1):
        print("\n" + "=" * 70)
        print(f"TEST CASE {index}: {query}")
        print("=" * 70)

        answer, context, routing = bot.ask(query, return_routing=True)

        print("\n[JEV AI / LAYA ROUTING DECISION]:")
        print("-" * 50)
        print(f"Intent:         {routing.get('intent')}")
        print(f"Confidence:     {routing.get('confidence')}")
        print(f"Route:          {routing.get('route')}")
        print(f"Target Course:  {routing.get('target_course')}")
        print(f"Target Aspect:  {routing.get('target_aspect')}")
        print(f"Supported:      {routing.get('is_supported')} (score: {routing.get('support_score')})")
        print(f"Source:         {routing.get('source')}")
        print("-" * 50)

        print("\n[RETRIEVED OKF CONTEXT]:")
        if context:
            print("-" * 50)
            print(context)
            print("-" * 50)
        else:
            print("<NO CONTEXT RETRIEVED / DIRECT RESPONSE>")

        print("\n[FINAL CHATBOT ANSWER]:")
        print("-" * 50)
        print(answer)
        print("-" * 50)

    bot.close()
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
