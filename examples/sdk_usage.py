import sys
import os
from dotenv import load_dotenv

# Load environment variables (api key, debug settings, etc.)
load_dotenv()
os.environ["DEBUG"] = "true"

# Add the parent directory (project root) to sys.path
# This allows running this script directly from the repo without installing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from liangent import Liangent  # noqa: E402

if __name__ == "__main__":
    print("--- Liangent SDK Example ---")

    # 1. Initialize Client
    # This will automatically load settings from .env (including DEBUG=True if set)
    try:
        client = Liangent(verbose=True,min_tool_use=2)
        print("Agent initialized.")
    except ValueError as e:
        print(f"Initialization Error: {e}")
        print("Please ensure you have a .env file or environment variables set.")
        exit(1)

    # 2. Define Query
    query = "计算 3*2"
    print(client.chat(query))
