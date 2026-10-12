"""
Convenience launcher for AI-Powered Intelligent Recruitment System.
Run: python run_app.py
"""

import sys
import subprocess
import os

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false"]
    print(f"Launching Streamlit application: {' '.join(cmd)}")
    subprocess.run(cmd)
