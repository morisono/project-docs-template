#!/usr/bin/env python3
"""Test script for googletrans library."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from googletrans import Translator


async def test_google_translate():
    """Test Google Translate functionality."""
    translator = Translator()

    try:
        print("Testing synchronous translation...")
        result = translator.translate("Hello world", dest="ja")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        if hasattr(result, "text"):
            print(f"Text: {result.text}")
        else:
            print("No text attribute")
    except Exception as e:
        print(f"Synchronous error: {e}")

    try:
        print("\nTesting async translation...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: translator.translate("Hello world", dest="ja")
        )
        print(f"Async result type: {type(result)}")
        print(f"Async result: {result}")
        if hasattr(result, "text"):
            print(f"Async text: {result.text}")
        else:
            print("No text attribute in async result")
    except Exception as e:
        print(f"Async error: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_translate())
