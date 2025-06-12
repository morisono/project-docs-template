#!/usr/bin/env python3
"""Example usage of the document translation system."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console

from translator.document_loader import DocumentLoader
from translator.language_detector import LanguageDetector
from translator.processor import DocumentTranslator
from translator.translation_service import TranslationManager

console = Console()


async def example_basic_usage():
    """Example 1: Basic directory translation."""
    console.print("[bold blue]Example 1: Basic Directory Translation[/bold blue]")

    # Create a temporary directory with test documents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create some test documents
        (temp_path / "english_doc.txt").write_text(
            "Hello world! This is a sample English document for translation testing."
        )
        (temp_path / "readme.md").write_text(
            "# Project Documentation\n\nThis is a markdown document with some content to translate."
        )

        # Create subdirectory
        subdir = temp_path / "subdirectory"
        subdir.mkdir()
        (subdir / "nested_doc.txt").write_text(
            "This is a nested document that should be translated while preserving structure."
        )

        console.print(f"Created test documents in: {temp_path}")

        # Initialize translator
        translator = DocumentTranslator()

        # Check if any translation services are available
        available_services = translator.translation_manager.get_available_services()
        if not available_services:
            console.print(
                "[red]No translation services configured. Please set API keys in .env file.[/red]"
            )
            console.print("Available options:")
            console.print("- OPENAI_API_KEY for OpenAI/ChatGPT")
            console.print("- DEEPSEEK_API_KEY for DeepSeek")
            console.print("- GOOGLE_TRANSLATE_API_KEY for Google Translate")
            return

        console.print(f"Available services: {', '.join(available_services)}")

        # Translate to a subset of languages for this example
        target_languages = ["ja", "ko"]  # Japanese and Korean

        console.print(f"Translating documents to: {', '.join(target_languages)}")

        try:
            results = await translator.translate_directory(
                source_directory=temp_path,
                target_languages=target_languages,
                output_directory=temp_path / "translated",
            )

            # Print results
            translator.print_results_summary(results)

            # Show the output structure
            console.print("\n[bold green]Output Structure:[/bold green]")
            output_dir = temp_path / "translated"
            if output_dir.exists():
                for item in sorted(output_dir.rglob("*")):
                    if item.is_file():
                        relative_path = item.relative_to(output_dir)
                        console.print(f"  📄 {relative_path}")

        except Exception as e:
            console.print(f"[red]Translation failed: {e}[/red]")


async def example_language_detection():
    """Example 2: Language detection capabilities."""
    console.print("\n[bold blue]Example 2: Language Detection[/bold blue]")

    detector = LanguageDetector()

    # Test texts in different languages
    test_texts = {
        "English": "This is a sample text in English language.",
        "Spanish": "Este es un texto de muestra en idioma español.",
        "French": "Ceci est un exemple de texte en langue française.",
        "Japanese": "これは日本語のサンプルテキストです。",
        "Korean": "이것은 한국어 샘플 텍스트입니다.",
    }

    console.print("Testing language detection:")
    for actual_lang, text in test_texts.items():
        detected = detector.detect_language(text)
        if detected:
            detected_name = detector.get_language_name(detected)
            status = "✓" if detected in ["en", "es", "fr", "ja", "ko"] else "?"
            console.print(
                f"  {status} {actual_lang}: detected as {detected_name} ({detected})"
            )
        else:
            console.print(f"  ✗ {actual_lang}: detection failed")


async def example_document_loading():
    """Example 3: Document loading capabilities."""
    console.print("\n[bold blue]Example 3: Document Loading[/bold blue]")

    loader = DocumentLoader()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files in different formats
        test_files = {
            "text_file.txt": "This is a plain text file.",
            "markdown_file.md": "# Markdown File\n\nThis is a **markdown** file with formatting.",
            "large_text.txt": "This is a longer text file. " * 100,  # Longer content
        }

        console.print("Testing document loading:")
        for filename, content in test_files.items():
            file_path = temp_path / filename
            file_path.write_text(content)

            loaded_content = await loader.load_document(file_path)
            if loaded_content:
                preview = (
                    loaded_content[:50] + "..."
                    if len(loaded_content) > 50
                    else loaded_content
                )
                console.print(
                    f"  ✓ {filename}: {len(loaded_content)} chars - '{preview}'"
                )
            else:
                console.print(f"  ✗ {filename}: loading failed")


async def example_translation_services():
    """Example 4: Translation service testing."""
    console.print("\n[bold blue]Example 4: Translation Services[/bold blue]")

    manager = TranslationManager()
    available_services = manager.get_available_services()

    if not available_services:
        console.print("[red]No translation services available.[/red]")
        return

    console.print(f"Available services: {', '.join(available_services)}")

    # Test translation with a simple phrase
    test_text = "Hello, how are you today?"
    target_language = "ja"  # Japanese

    console.print(f"\nTesting translation: '{test_text}' -> {target_language}")

    try:
        result = await manager.translate(test_text, target_language, "en")
        if result:
            console.print(f"  ✓ Translation result: '{result}'")
        else:
            console.print("  ✗ Translation failed")
    except Exception as e:
        console.print(f"  ✗ Translation error: {e}")


async def example_batch_processing():
    """Example 5: Batch processing with progress tracking."""
    console.print("\n[bold blue]Example 5: Batch Processing[/bold blue]")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create multiple test documents
        console.print("Creating test documents...")
        for i in range(5):
            content = f"This is test document number {i + 1}. " * 10
            (temp_path / f"doc_{i + 1}.txt").write_text(content)

        # Create nested structure
        for lang in ["en", "draft"]:
            lang_dir = temp_path / lang
            lang_dir.mkdir()
            for i in range(3):
                content = f"This is {lang} document {i + 1}. " * 5
                (lang_dir / f"{lang}_doc_{i + 1}.txt").write_text(content)

        console.print(f"Created test documents in: {temp_path}")

        # List all created files
        all_files = list(temp_path.rglob("*.txt"))
        console.print(f"Total files: {len(all_files)}")

        # Initialize translator with smaller batch size for demo
        translator = DocumentTranslator()
        translator.config.batch_size = 2  # Process 2 files at a time

        # Check if services are available
        if not translator.translation_manager.get_available_services():
            console.print(
                "[red]No translation services available for batch processing demo.[/red]"
            )
            return

        # Translate to just one language for demo
        try:
            results = await translator.translate_directory(
                source_directory=temp_path,
                target_languages=["ja"],  # Just Japanese
                output_directory=temp_path / "batch_translated",
            )

            console.print("\nBatch processing completed:")
            console.print(f"  Total files processed: {len(results)}")
            console.print(f"  Successful: {sum(1 for r in results if r.success)}")
            console.print(f"  Failed: {sum(1 for r in results if not r.success)}")

        except Exception as e:
            console.print(f"[red]Batch processing failed: {e}[/red]")


async def main():
    """Run all examples."""
    console.print(
        "[bold green]Document Translation System - Usage Examples[/bold green]"
    )
    console.print("=" * 60)

    # Check if we have API keys configured
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_TRANSLATE_API_KEY"))

    console.print("API Configuration:")
    console.print(f"  OpenAI: {'✓' if has_openai else '✗'}")
    console.print(f"  DeepSeek: {'✓' if has_deepseek else '✗'}")
    console.print(f"  Google Translate: {'✓' if has_google else '✗'}")

    if not (has_openai or has_deepseek or has_google):
        console.print(
            "\n[yellow]Note: No API keys found. Some examples will show configuration info only.[/yellow]"
        )
        console.print(
            "To enable full functionality, copy .env.example to .env and add your API keys."
        )

    console.print("\n")

    # Run examples
    await example_language_detection()
    await example_document_loading()
    await example_translation_services()
    await example_basic_usage()
    await example_batch_processing()

    console.print("\n[bold green]Examples completed![/bold green]")
    console.print("\nFor more information, see TRANSLATION_README.md")


if __name__ == "__main__":
    asyncio.run(main())
