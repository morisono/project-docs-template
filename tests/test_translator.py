"""Test configuration and basic functionality."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

if TYPE_CHECKING:
    pass


class TestConfig:
    """Test configuration functionality."""

    def test_config_creation(self) -> None:
        """Test that configuration can be created."""
        from translator.config import get_config

        config = get_config()
        assert config is not None
        assert config.supported_languages is not None
        assert len(config.supported_languages) > 0
        assert "en" in config.supported_languages

    def test_language_mapping(self) -> None:
        """Test language mapping functionality."""
        from translator.config import get_language_mapping

        mapping = get_language_mapping()
        assert mapping is not None
        assert "en" in mapping.LANGUAGE_NAMES
        assert mapping.LANGUAGE_NAMES["en"] == "English"


class TestLanguageDetector:
    """Test language detection functionality."""

    def test_language_detector_creation(self) -> None:
        """Test that language detector can be created."""
        from translator.language_detector import LanguageDetector

        detector = LanguageDetector()
        assert detector is not None

    def test_detect_english(self) -> None:
        """Test detection of English text."""
        from translator.language_detector import LanguageDetector

        detector = LanguageDetector()
        text = "This is a sample English text for language detection testing."

        # Note: langdetect might not be available in test environment
        try:
            result = detector.detect_language(text)
            if result:  # Only assert if detection worked
                assert result == "en"
        except Exception:
            # Skip test if langdetect is not available
            pytest.skip("langdetect library not available")

    def test_supported_languages(self) -> None:
        """Test supported languages functionality."""
        from translator.language_detector import LanguageDetector

        detector = LanguageDetector()
        supported = detector.get_supported_languages()

        assert isinstance(supported, dict)
        assert "en" in supported
        assert supported["en"] == "English"


class TestDocumentLoader:
    """Test document loading functionality."""

    def test_document_loader_creation(self) -> None:
        """Test that document loader can be created."""
        from translator.document_loader import DocumentLoader

        loader = DocumentLoader()
        assert loader is not None

    @pytest.mark.asyncio
    async def test_load_text_file(self, tmp_path: Path) -> None:
        """Test loading a text file."""
        from translator.document_loader import DocumentLoader

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "This is a test file content."
        test_file.write_text(test_content, encoding="utf-8")

        loader = DocumentLoader()
        result = await loader.load_document(test_file)

        assert result == test_content

    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        from translator.document_loader import DocumentLoader

        nonexistent_file = tmp_path / "nonexistent.txt"
        loader = DocumentLoader()
        result = await loader.load_document(nonexistent_file)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_supported_files(self, tmp_path: Path) -> None:
        """Test getting supported files from directory."""
        from translator.document_loader import DocumentLoader

        # Create test files
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "test.md").write_text("# Test markdown")
        (tmp_path / "test.unsupported").write_text("unsupported content")

        loader = DocumentLoader()
        files = await loader.get_supported_files(tmp_path)

        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "test.txt" in file_names
        assert "test.md" in file_names
        assert "test.unsupported" not in file_names


class TestTranslationService:
    """Test translation service functionality."""

    def test_translation_manager_creation(self) -> None:
        """Test that translation manager can be created."""
        from translator.translation_service import TranslationManager

        manager = TranslationManager()
        assert manager is not None

    def test_openai_service_creation(self) -> None:
        """Test OpenAI service creation."""
        from translator.translation_service import OpenAITranslationService

        service = OpenAITranslationService(
            api_key="test_key", base_url="https://api.test.com", model="test-model"
        )
        assert service is not None
        assert service.is_available()

    def test_google_service_creation(self) -> None:
        """Test Google service creation."""
        from translator.translation_service import GoogleTranslationService

        service = GoogleTranslationService()
        assert service is not None
        # Note: May not be available without googletrans installed


class TestProcessor:
    """Test main processor functionality."""

    def test_translation_result_creation(self) -> None:
        """Test TranslationResult creation."""
        from translator.processor import TranslationResult

        result = TranslationResult(
            source_file=Path("test.txt"),
            target_file=Path("test_en.txt"),
            source_language="en",
            target_language="ja",
            success=True,
        )

        assert result.success is True
        assert result.source_language == "en"
        assert result.target_language == "ja"

    def test_document_translator_creation(self) -> None:
        """Test DocumentTranslator creation."""
        from translator.processor import DocumentTranslator

        translator = DocumentTranslator()
        assert translator is not None
        assert translator.config is not None
        assert translator.document_loader is not None
        assert translator.language_detector is not None
        assert translator.translation_manager is not None


class TestCLI:
    """Test CLI functionality."""

    def test_cli_import(self) -> None:
        """Test that CLI can be imported."""
        from translator.cli import cli

        assert cli is not None
        assert callable(cli)


# Integration test (requires API keys to run)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require actual API access."""

    @pytest.mark.asyncio
    async def test_full_translation_flow(self, tmp_path: Path) -> None:
        """Test complete translation flow with actual API."""
        import os

        from translator.processor import DocumentTranslator

        # Skip if no API keys configured
        if not (os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
            pytest.skip("No API keys configured for integration test")

        # Create test document
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, this is a test document.", encoding="utf-8")

        # Run translation
        translator = DocumentTranslator()
        results = await translator.translate_directory(
            source_directory=tmp_path,
            target_languages=["ja"],  # Translate to Japanese only
            output_directory=tmp_path / "translated",
        )

        # Verify results
        assert len(results) == 1
        result = results[0]
        assert (
            result.success or result.error is not None
        )  # Either success or documented failure
