"""
Main entry point for the Vinted monitoring service.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import cli

if __name__ == '__main__':
    cli()
