"""Main translation processor for batch document translation."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from loguru import logger
from rich.console import Console
from rich.progress import Progress, TaskID

from .config import get_config
from .document_loader import DocumentLoader
from .language_detector import LanguageDetector
from .translation_service import TranslationManager

if TYPE_CHECKING:
    pass


class TranslationResult:
    """Result of a translation operation."""

    def __init__(
        self,
        source_file: Path,
        target_file: Path,
        source_language: str | None,
        target_language: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Initialize a translation result.

        Args:
            source_file: Source file path
            target_file: Target file path
            source_language: Detected source language
            target_language: Target language
            success: Whether translation was successful
            error: Error message if failed
        """
        self.source_file = source_file
        self.target_file = target_file
        self.source_language = source_language
        self.target_language = target_language
        self.success = success
        self.error = error


class DocumentTranslator:
    """Main document translator with batch processing capabilities."""

    def __init__(self) -> None:
        """Initialize the document translator."""
        self.config = get_config()
        self.document_loader = DocumentLoader()
        self.language_detector = LanguageDetector()
        self.translation_manager = TranslationManager()
        self.console = Console()

    async def translate_directory(
        self,
        source_directory: Path,
        target_languages: list[str] | None = None,
        output_directory: Path | None = None,
    ) -> list[TranslationResult]:
        """Translate all supported documents in a directory.

        Args:
            source_directory: Directory containing source documents
            target_languages: List of target language codes (defaults to all supported)
            output_directory: Output directory (defaults to config setting)

        Returns:
            List of translation results
        """
        if not source_directory.exists() or not source_directory.is_dir():
            raise ValueError(f"Source directory does not exist: {source_directory}")

        # Use configured target languages if none specified
        if target_languages is None:
            target_languages = self.config.supported_languages.copy()

        # Set up output directory
        if output_directory is None:
            output_directory = source_directory / self.config.output_directory
        output_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting translation of directory: {source_directory}")
        logger.info(f"Target languages: {target_languages}")
        logger.info(f"Output directory: {output_directory}")

        # Get all supported files
        supported_files = await self.document_loader.get_supported_files(
            source_directory
        )
        if not supported_files:
            logger.warning("No supported files found in source directory")
            return []

        logger.info(f"Found {len(supported_files)} supported files")

        # Process files in batches
        results = []
        semaphore = asyncio.Semaphore(self.config.batch_size)

        with Progress() as progress:
            task = progress.add_task(
                "Translating documents...",
                total=len(supported_files) * len(target_languages),
            )

            async def process_file_language_pair(
                file_path: Path, target_lang: str, task_id: TaskID
            ) -> TranslationResult:
                async with semaphore:
                    result = await self._translate_single_file(
                        file_path, target_lang, source_directory, output_directory
                    )
                    progress.update(task_id, advance=1)
                    return result

            # Create tasks for all file-language combinations
            tasks = []
            for file_path in supported_files:
                for target_lang in target_languages:
                    task_coro = process_file_language_pair(file_path, target_lang, task)
                    tasks.append(task_coro)

            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for result in results:
            if isinstance(result, TranslationResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Translation task failed: {result}")

        # Log summary
        successful = sum(1 for r in valid_results if r.success)
        failed = len(valid_results) - successful
        logger.info(f"Translation completed: {successful} successful, {failed} failed")

        return valid_results

    async def _translate_single_file(
        self,
        file_path: Path,
        target_language: str,
        source_directory: Path,
        output_directory: Path,
    ) -> TranslationResult:
        """Translate a single file to a target language.

        Args:
            file_path: Path to the source file
            target_language: Target language code
            source_directory: Base source directory
            output_directory: Base output directory

        Returns:
            Translation result
        """
        try:
            # Generate output file path
            relative_path = file_path.relative_to(source_directory)
            target_file = self._generate_output_path(
                relative_path, target_language, output_directory
            )

            # Skip if file already exists and not overwriting
            if target_file.exists() and not self.config.overwrite_existing:
                logger.info(f"Skipping existing file: {target_file}")
                return TranslationResult(
                    source_file=file_path,
                    target_file=target_file,
                    source_language=None,
                    target_language=target_language,
                    success=True,
                )

            # Load document content
            logger.info(f"Loading document: {file_path}")
            content = await self.document_loader.load_document(file_path)
            if not content:
                error_msg = "Failed to load document content"
                logger.error(f"{error_msg}: {file_path}")
                return TranslationResult(
                    source_file=file_path,
                    target_file=target_file,
                    source_language=None,
                    target_language=target_language,
                    success=False,
                    error=error_msg,
                )

            # Detect source language
            logger.info(f"Detecting language for: {file_path}")
            source_language = self.language_detector.detect_language(content)

            # Skip if already in target language
            if source_language == target_language:
                logger.info(
                    f"Document already in target language ({target_language}): {file_path}"
                )
                return TranslationResult(
                    source_file=file_path,
                    target_file=target_file,
                    source_language=source_language,
                    target_language=target_language,
                    success=True,
                )

            # Translate content
            logger.info(
                f"Translating {file_path} from {source_language} to {target_language}"
            )
            translated_content = await self.translation_manager.translate(
                content, target_language, source_language
            )

            if not translated_content:
                error_msg = "Translation failed"
                logger.error(f"{error_msg}: {file_path}")
                return TranslationResult(
                    source_file=file_path,
                    target_file=target_file,
                    source_language=source_language,
                    target_language=target_language,
                    success=False,
                    error=error_msg,
                )

            # Save translated content
            await self._save_translated_content(translated_content, target_file)
            logger.info(f"Saved translation: {target_file}")

            return TranslationResult(
                source_file=file_path,
                target_file=target_file,
                source_language=source_language,
                target_language=target_language,
                success=True,
            )

        except Exception as e:
            logger.error(f"Error translating {file_path}: {e}")
            return TranslationResult(
                source_file=file_path,
                target_file=target_file
                if "target_file" in locals()
                else Path("unknown"),
                source_language=source_language
                if "source_language" in locals()
                else None,
                target_language=target_language,
                success=False,
                error=str(e),
            )

    def _generate_output_path(
        self, relative_path: Path, target_language: str, output_directory: Path
    ) -> Path:
        """Generate output file path for translated content.

        Args:
            relative_path: Relative path from source directory
            target_language: Target language code
            output_directory: Base output directory

        Returns:
            Output file path
        """
        if self.config.preserve_structure:
            # Create language-specific subdirectory
            lang_dir = output_directory / target_language
            target_file = lang_dir / relative_path
        else:
            # Flat structure with language suffix
            stem = relative_path.stem
            suffix = relative_path.suffix
            filename = f"{stem}_{target_language}{suffix}"
            target_file = output_directory / filename

        # Ensure parent directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)
        return target_file

    async def _save_translated_content(self, content: str, target_file: Path) -> None:
        """Save translated content to file.

        Args:
            content: Translated content
            target_file: Target file path
        """
        async with aiofiles.open(target_file, "w", encoding="utf-8") as file:
            await file.write(content)

    def print_results_summary(self, results: list[TranslationResult]) -> None:
        """Print a summary of translation results.

        Args:
            results: List of translation results
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        self.console.print("\n[bold green]Translation Summary[/bold green]")
        self.console.print(f"Total files processed: {len(results)}")
        self.console.print(f"Successful: {len(successful)}")
        self.console.print(f"Failed: {len(failed)}")

        if failed:
            self.console.print("\n[bold red]Failed Translations:[/bold red]")
            for result in failed:
                self.console.print(
                    f"  {result.source_file} -> {result.target_language}: {result.error}"
                )

        # Group successful translations by language
        by_language = {}
        for result in successful:
            if result.target_language not in by_language:
                by_language[result.target_language] = []
            by_language[result.target_language].append(result)

        if by_language:
            self.console.print(
                "\n[bold green]Successful Translations by Language:[/bold green]"
            )
            for lang, lang_results in by_language.items():
                lang_name = self.language_detector.get_language_name(lang)
                self.console.print(f"  {lang_name} ({lang}): {len(lang_results)} files")
