#!/usr/bin/env python3
"""
Development runner script for Task Tracker.

This script helps run both the backend API and frontend application
for development purposes.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def check_requirements():
    """Check if required tools are installed."""
    print("Checking requirements...")

    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"],
                              capture_output=True, text=True, check=True)
        print(f"[OK] Python: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("Python not found")
        return False

    return True

def setup_backend():
    """Set up the backend environment."""
    print("\nSetting up backend...")

    # Check if virtual environment exists
    if not Path("venv").exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate.bat"
        pip_path = "venv\\Scripts\\pip.exe"
    else:  # Unix/Linux
        activate_script = "source venv/bin/activate"
        pip_path = "venv/bin/pip"

    print("Installing backend dependencies...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)

    print("[OK] Backend setup complete")

def run_backend():
    """Run the backend server."""
    print("\nStarting backend server...")

    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python.exe"
    else:  # Unix/Linux
        python_path = "venv/bin/python"

    # Set environment variable for Python path
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'

    return subprocess.Popen([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ], env=env)

def main():
    """Main function to run the development environment."""
    print("Task Tracker Development Runner")
    print("=" * 50)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "setup":
            if not check_requirements():
                sys.exit(1)

            setup_backend()
            print("\nSetup complete! Run 'python run.py' to start the backend server.")

        elif command == "backend":
            if not check_requirements():
                sys.exit(1)
            backend_process = run_backend()
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                backend_process.terminate()
                backend_process.wait()

        else:
            print("Usage: python run.py [command]")
            print("Commands:")
            print("  setup   - Set up the backend environment")
            print("  backend - Run the backend server")
            print("  (no args) - Run the backend server (default)")

    else:
        # Default to backend command
        if not check_requirements():
            sys.exit(1)
        backend_process = run_backend()
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            backend_process.terminate()
            backend_process.wait()

def main_with_args(args):
    """Helper function to call main with specific args."""
    original_argv = sys.argv
    sys.argv = args
    try:
        main()
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    main()
