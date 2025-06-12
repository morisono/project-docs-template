#!/usr/bin/env python3
"""Document Translation System - Main entry point.

This script provides a comprehensive document translation system that:
- Automatically detects document language
- Translates to multiple target languages
- Supports various document formats (TXT, MD, PDF, DOCX, DOC, RTF)
- Uses multiple translation services with fallback support
- Provides batch processing with progress tracking
- Maintains directory structure in output

Usage Examples:
    # Translate all documents in a directory to all supported languages
    python translate.py translate ./docs

    # Translate to specific languages
    python translate.py translate ./docs --languages en ja ko

    # Specify output directory
    python translate.py translate ./docs --output ./translated --overwrite

    # Check configuration
    python translate.py config-info

    # List supported languages
    python translate.py languages

    # Detect language of a specific file
    python translate.py detect-language ./docs/README.md

Environment Variables:
    OPENAI_API_KEY: OpenAI API key
    DEEPSEEK_API_KEY: DeepSeek API key
    GOOGLE_TRANSLATE_API_KEY: Google Translate API key

Requirements:
    pip install openai langdetect googletrans python-docx PyPDF2 aiofiles
    pip install aiohttp tqdm loguru pydantic pydantic-settings click rich tenacity
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from translator.cli import cli

if __name__ == "__main__":
    cli()
