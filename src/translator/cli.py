"""Command-line interface for the document translator."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import click
from loguru import logger
from rich.console import Console

from .config import get_config
from .processor import DocumentTranslator

if TYPE_CHECKING:
    pass


console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--log-file", type=str, help="Log file path")
def cli(verbose: bool, log_file: str | None) -> None:
    """Document Translation System - Automatically translate documents to multiple languages."""
    # Configure logging
    config = get_config()
    log_level = "DEBUG" if verbose else config.log_level

    # Remove default logger
    logger.remove()

    # Add console logger
    logger.add(
        lambda msg: console.print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
    )

    # Add file logger if specified
    if log_file or config.log_file:
        logger.add(
            log_file or config.log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
        )


@cli.command()
@click.argument(
    "source_directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--languages", "-l", multiple=True, help="Target languages (e.g., 'en', 'ja', 'ko')"
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output directory"
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing translations")
@click.option(
    "--batch-size", type=int, help="Number of documents to process in parallel"
)
def translate(
    source_directory: Path,
    languages: tuple[str, ...],
    output: Path | None,
    overwrite: bool,
    batch_size: int | None,
) -> None:
    """Translate all documents in a directory to specified languages."""

    async def run_translation() -> None:
        """Run the translation process asynchronously."""
        try:
            # Initialize translator
            translator = DocumentTranslator()

            # Override config settings if provided
            if overwrite:
                translator.config.overwrite_existing = overwrite
            if batch_size:
                translator.config.batch_size = batch_size

            # Convert languages tuple to list if provided
            target_languages = list(languages) if languages else None

            console.print(
                f"[bold blue]Starting translation of: {source_directory}[/bold blue]"
            )
            if target_languages:
                console.print(f"Target languages: {', '.join(target_languages)}")
            else:
                console.print("Using all supported languages")

            # Run translation
            results = await translator.translate_directory(
                source_directory=source_directory,
                target_languages=target_languages,
                output_directory=output,
            )

            # Print results
            translator.print_results_summary(results)

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            console.print(f"[bold red]Error: {e}[/bold red]")
            raise click.ClickException(str(e)) from e

    # Run the async function
    asyncio.run(run_translation())


@cli.command()
def languages() -> None:
    """List all supported languages."""
    config = get_config()

    console.print("[bold blue]Supported Languages:[/bold blue]")
    console.print()

    # Create table-like output
    for code in sorted(config.supported_languages):
        from .language_detector import LanguageDetector

        detector = LanguageDetector()
        name = detector.get_language_name(code)
        console.print(f"  {code:<8} - {name}")


@cli.command()
def config_info() -> None:
    """Show current configuration."""
    config = get_config()

    console.print("[bold blue]Current Configuration:[/bold blue]")
    console.print()

    # API Configuration
    console.print("[bold]API Configuration:[/bold]")
    console.print(f"  OpenAI API Key: {'✓' if config.openai_api_key else '✗'}")
    console.print(f"  OpenAI Base URL: {config.openai_base_url}")
    console.print(f"  DeepSeek API Key: {'✓' if config.deepseek_api_key else '✗'}")
    console.print(f"  DeepSeek Base URL: {config.deepseek_base_url}")
    console.print(
        f"  Google Translate API Key: {'✓' if config.google_translate_api_key else '✗'}"
    )
    console.print()

    # Translation Settings
    console.print("[bold]Translation Settings:[/bold]")
    console.print(f"  Default Model: {config.default_model}")
    console.print(f"  Max Retries: {config.max_retries}")
    console.print(f"  Retry Delay: {config.retry_delay}s")
    console.print(f"  Batch Size: {config.batch_size}")
    console.print(f"  Max File Size: {config.max_file_size_mb} MB")
    console.print()

    # File Settings
    console.print("[bold]File Settings:[/bold]")
    console.print(f"  Supported Extensions: {', '.join(config.supported_extensions)}")
    console.print(f"  Output Directory: {config.output_directory}")
    console.print(f"  Preserve Structure: {config.preserve_structure}")
    console.print(f"  Overwrite Existing: {config.overwrite_existing}")
    console.print()

    # Check available services
    from .translation_service import TranslationManager

    manager = TranslationManager()
    available_services = manager.get_available_services()

    console.print("[bold]Available Translation Services:[/bold]")
    if available_services:
        for service in available_services:
            console.print(f"  ✓ {service}")
    else:
        console.print("  [red]No translation services configured![/red]")


@cli.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
def detect_language(file_path: Path) -> None:
    """Detect the language of a specific file."""

    async def run_detection() -> None:
        """Run language detection asynchronously."""
        try:
            from .document_loader import DocumentLoader
            from .language_detector import LanguageDetector

            # Load document
            loader = DocumentLoader()
            content = await loader.load_document(file_path)

            if not content:
                console.print(f"[red]Failed to load content from: {file_path}[/red]")
                return

            # Detect language
            detector = LanguageDetector()
            detected_lang = detector.detect_language(content)

            if detected_lang:
                lang_name = detector.get_language_name(detected_lang)
                console.print("[bold green]Detected Language:[/bold green]")
                console.print(f"  File: {file_path}")
                console.print(f"  Language: {lang_name} ({detected_lang})")

                # Show confidence scores
                lang_probs = detector.detect_language_with_confidence(content)
                if len(lang_probs) > 1:
                    console.print("[bold]All detected languages:[/bold]")
                    for lang_code, confidence in lang_probs:
                        lang_name = detector.get_language_name(lang_code)
                        console.print(f"  {lang_name} ({lang_code}): {confidence:.2%}")
            else:
                console.print(f"[red]Could not detect language for: {file_path}[/red]")

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            console.print(f"[bold red]Error: {e}[/bold red]")

    # Run the async function
    asyncio.run(run_detection())


if __name__ == "__main__":
    cli()
