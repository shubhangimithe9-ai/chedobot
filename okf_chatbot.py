import sys
from pathlib import Path

# Ensure project root is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import main

if __name__ == "__main__":
    main()
