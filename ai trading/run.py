"""
run.py - Single-command runner for the AI Trading Research Assistant.
"""

import sys
import os

# Add backend to sys.path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if __name__ == "__main__":
    import uvicorn
    print("\n=======================================================")
    print("[*] Antigravity AI Trading Research Assistant Prototype")
    print("=======================================================")
    print("Serving on: http://127.0.0.1:8000")
    print("Press Ctrl+C to terminate server.")
    print("=======================================================\n")
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
