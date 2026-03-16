# src/main.py
import sys
import os

# Ensure we can import modules from 'src' if running from outside
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import TeaApp
from services.logger import Logger # We will build this next

logger = Logger()

def main():
    logger.info("Starting Ratea 2.0...")

    app = TeaApp()
    try:
        app.run()
    except Exception as e:
        logger.critical(f"App crashed: {e}")
        raise e

if __name__ == "__main__":
    main()