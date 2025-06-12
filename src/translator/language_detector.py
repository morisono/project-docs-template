"""Language detection utilities."""

from typing import TYPE_CHECKING

from langdetect import detect, detect_langs
from loguru import logger

from .config import get_language_mapping

if TYPE_CHECKING:
    pass


class LanguageDetector:
    """Detect the language of text content."""

    def __init__(self) -> None:
        """Initialize the language detector."""
        self.language_mapping = get_language_mapping()

    def detect_language(self, text: str) -> str | None:
        """Detect the language of the given text.

        Args:
            text: Text content to analyze

        Returns:
            Detected language code or None if detection failed
        """
        if not text or not text.strip():
            return None

        try:
            # Use langdetect to identify the language
            detected_lang = detect(text)

            # Map to our supported language codes
            mapped_lang = self._map_langdetect_code(detected_lang)

            logger.info(f"Detected language: {detected_lang} -> {mapped_lang}")
            return mapped_lang

        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return None

    def detect_language_with_confidence(self, text: str) -> list[tuple[str, float]]:
        """Detect languages with confidence scores.

        Args:
            text: Text content to analyze

        Returns:
            List of (language_code, confidence) tuples, sorted by confidence
        """
        if not text or not text.strip():
            return []

        try:
            # Get language probabilities
            lang_probs = detect_langs(text)

            # Map to our supported codes and return with confidence
            results = []
            for lang_prob in lang_probs:
                mapped_lang = self._map_langdetect_code(lang_prob.lang)
                if mapped_lang:
                    results.append((mapped_lang, lang_prob.prob))

            return results

        except Exception as e:
            logger.error(f"Error detecting language with confidence: {e}")
            return []

    def _map_langdetect_code(self, langdetect_code: str) -> str | None:
        """Map langdetect language code to our supported codes.

        Args:
            langdetect_code: Language code from langdetect

        Returns:
            Mapped language code or None if not supported
        """
        # Direct mapping for exact matches
        for our_code, detect_code in self.language_mapping.LANGDETECT_CODES.items():
            if detect_code == langdetect_code:
                return our_code

        # Handle special cases
        if langdetect_code == "zh-cn":
            return "zh"
        elif langdetect_code == "zh-tw":
            return "zh-tw"

        # If no mapping found, check if it's already one of our codes
        if langdetect_code in self.language_mapping.LANGUAGE_NAMES:
            return langdetect_code

        return None

    def is_supported_language(self, language_code: str) -> bool:
        """Check if a language code is supported.

        Args:
            language_code: Language code to check

        Returns:
            True if the language is supported
        """
        return language_code in self.language_mapping.LANGUAGE_NAMES

    def get_language_name(self, language_code: str) -> str:
        """Get the human-readable name for a language code.

        Args:
            language_code: Language code

        Returns:
            Human-readable language name
        """
        return self.language_mapping.LANGUAGE_NAMES.get(language_code, language_code)

    def get_supported_languages(self) -> dict[str, str]:
        """Get all supported languages with their names.

        Returns:
            Dictionary mapping language codes to names
        """
        return self.language_mapping.LANGUAGE_NAMES.copy()
