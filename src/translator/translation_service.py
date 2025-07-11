"""Translation service implementations."""

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_config, get_language_mapping

if TYPE_CHECKING:
    pass

try:
    from googletrans import Translator as GoogleTranslator

    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False
    GoogleTranslator = None


class TranslationService(ABC):
    """Abstract base class for translation services."""

    @abstractmethod
    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if failed
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the translation service is available."""


class OpenAITranslationService(TranslationService):
    """OpenAI/DeepSeek translation service using chat completions."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
    ) -> None:
        """Initialize the OpenAI translation service.

        Args:
            api_key: API key for the service
            base_url: Base URL for the API
            model: Model to use for translation
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.language_mapping = get_language_mapping()

    def is_available(self) -> bool:
        """Check if the service is available."""
        return bool(self.client.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text using OpenAI chat completions.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if failed
        """
        try:
            # Get language names for better prompts
            target_name = self.language_mapping.LANGUAGE_NAMES.get(
                target_language, target_language
            )
            source_name = (
                self.language_mapping.LANGUAGE_NAMES.get(
                    source_language, "auto-detected"
                )
                if source_language
                else "auto-detected"
            )

            # Create translation prompt
            system_prompt = (
                "You are a professional translator. Translate the given text accurately while preserving "
                "formatting, structure, and meaning. Maintain any markdown formatting, code blocks, "
                "links, and special characters. Only return the translated text without any explanations."
            )

            user_prompt = f"Translate the following text from {source_name} to {target_name}:\n\n{text}"

            # Make the API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent translations
                max_tokens=4000,
            )

            translated_text = response.choices[0].message.content
            if translated_text:
                return translated_text.strip()

            logger.error("Empty response from OpenAI translation service")
            return None

        except Exception as e:
            logger.error(f"Error in OpenAI translation: {e}")
            return None


class GoogleTranslationService(TranslationService):
    """Google Translate service implementation."""

    def __init__(self) -> None:
        """Initialize the Google translation service."""
        self.translator = GoogleTranslator() if HAS_GOOGLETRANS else None
        self.language_mapping = get_language_mapping()

    def is_available(self) -> bool:
        """Check if the service is available."""
        return HAS_GOOGLETRANS and self.translator is not None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text using Google Translate.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if failed
        """
        if not self.is_available():
            logger.error("Google Translate service not available")
            return None

        try:
            # Map our language codes to Google Translate codes
            target_code = self.language_mapping.GOOGLE_TRANSLATE_CODES.get(
                target_language, target_language
            )
            source_code = (
                self.language_mapping.GOOGLE_TRANSLATE_CODES.get(
                    source_language, "auto"
                )
                if source_language
                else "auto"
            )

            # Run the synchronous translation in an executor to avoid blocking
            loop = asyncio.get_event_loop()

            def _translate():
                """Synchronous translation function."""
                try:
                    result = self.translator.translate(
                        text, dest=target_code, src=source_code
                    )
                    # Check if result is a coroutine (shouldn't be with googletrans)
                    if hasattr(result, "__await__"):
                        logger.error(
                            "Got coroutine from googletrans - version compatibility issue"
                        )
                        return None
                    return result
                except Exception as e:
                    logger.error(f"Error in synchronous translation: {e}")
                    return None

            result = await loop.run_in_executor(None, _translate)

            if result and hasattr(result, "text") and result.text:
                return result.text.strip()

            logger.error("Empty response from Google Translate service")
            return None

        except Exception as e:
            logger.error(f"Error in Google translation: {e}")
            return None


class MyMemoryTranslationService(TranslationService):
    """MyMemory translation service implementation (free API)."""

    def __init__(self) -> None:
        """Initialize the MyMemory translation service."""
        self.base_url = "https://api.mymemory.translated.net/get"
        self.language_mapping = get_language_mapping()

    def is_available(self) -> bool:
        """Check if the service is available."""
        return True  # MyMemory doesn't require API keys

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text using MyMemory API.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if failed
        """
        try:
            import aiohttp

            # Map language codes
            target_code = self.language_mapping.MYMEMORY_CODES.get(
                target_language, target_language
            )
            source_code = (
                self.language_mapping.MYMEMORY_CODES.get(
                    source_language, source_language
                )
                if source_language
                else "auto"
            )

            # MyMemory expects format like "en|it" for source|target
            if source_code == "auto":
                lang_pair = target_code
            else:
                lang_pair = f"{source_code}|{target_code}"

            params = {
                "q": text,
                "langpair": lang_pair,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if (
                            data.get("responseStatus") == 200
                            and "responseData" in data
                            and "translatedText" in data["responseData"]
                        ):
                            translated_text = data["responseData"]["translatedText"]
                            if translated_text and translated_text.strip():
                                return translated_text.strip()

            logger.error("Failed to get valid response from MyMemory")
            return None

        except Exception as e:
            logger.error(f"Error in MyMemory translation: {e}")
            return None


class LibreTranslateService(TranslationService):
    """LibreTranslate service implementation (free, self-hosted)."""

    def __init__(self, api_url: str = "https://libretranslate.de/translate") -> None:
        """Initialize the LibreTranslate service.

        Args:
            api_url: LibreTranslate API URL
        """
        self.api_url = api_url
        self.language_mapping = get_language_mapping()

    def is_available(self) -> bool:
        """Check if the service is available."""
        return True  # LibreTranslate public instance doesn't require API keys

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text using LibreTranslate API.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if failed
        """
        try:
            import aiohttp

            # Map language codes
            target_code = self.language_mapping.LIBRETRANSLATE_CODES.get(
                target_language, target_language
            )
            source_code = (
                self.language_mapping.LIBRETRANSLATE_CODES.get(
                    source_language, source_language
                )
                if source_language
                else "auto"
            )

            data = {
                "q": text,
                "source": source_code,
                "target": target_code,
                "format": "text",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "translatedText" in result:
                            translated_text = result["translatedText"]
                            if translated_text and translated_text.strip():
                                return translated_text.strip()

            logger.error("Failed to get valid response from LibreTranslate")
            return None

        except Exception as e:
            logger.error(f"Error in LibreTranslate translation: {e}")
            return None


class MockTranslationService(TranslationService):
    """Mock translation service for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock translation service."""
        self.language_mapping = get_language_mapping()

    def is_available(self) -> bool:
        """Check if the service is available."""
        return True

    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Mock translate text by adding language prefix.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Mock translated text
        """
        try:
            # Get language name for target
            target_name = self.language_mapping.LANGUAGE_NAMES.get(
                target_language, target_language
            )

            # Simple mock translation: add language prefix
            # mock_translation = f"[{target_name.upper()} TRANSLATION]\n\n{text}" # noqa
            mock_translation = ""
            return mock_translation
        except Exception as e:
            logger.error(f"Error in mock translation: {e}")
            return None


class TranslationManager:
    """Manage multiple translation services with fallback support."""

    def __init__(self) -> None:
        """Initialize the translation manager."""
        self.config = get_config()
        self.services: list[TranslationService] = []
        self._setup_services()

    def _setup_services(self) -> None:
        """Set up available translation services."""
        # Add OpenAI/DeepSeek service if configured
        if self.config.openai_api_key:
            openai_service = OpenAITranslationService(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url,
                model=self.config.default_model,
            )
            self.services.append(openai_service)
            logger.info(
                f"Added OpenAI service with base URL: {self.config.openai_base_url}"
            )

        # Add DeepSeek service if configured separately
        if self.config.deepseek_api_key:
            deepseek_service = OpenAITranslationService(
                api_key=self.config.deepseek_api_key,
                base_url=self.config.deepseek_base_url,
                model=self.config.default_model,
            )
            self.services.append(deepseek_service)
            logger.info("Added DeepSeek service")

        # Add Google Translate service if available
        google_service = GoogleTranslationService()
        if google_service.is_available():
            self.services.append(google_service)
            logger.info("Added Google Translate service")

        # Add MyMemory translation service
        mymemory_service = MyMemoryTranslationService()
        if mymemory_service.is_available():
            self.services.append(mymemory_service)
            logger.info("Added MyMemory translation service")

        # Add LibreTranslate service
        libre_service = LibreTranslateService()
        if libre_service.is_available():
            self.services.append(libre_service)
            logger.info("Added LibreTranslate service")

        # Add Mock translation service
        mock_service = MockTranslationService()
        if mock_service.is_available():
            self.services.append(mock_service)
            logger.info("Added Mock translation service")

        if not self.services:
            logger.warning("No translation services configured!")

    async def translate(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str | None:
        """Translate text using available services with fallback.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated text or None if all services failed
        """
        if not text or not text.strip():
            return None

        if not self.services:
            logger.error("No translation services available")
            return None

        # Try each service in order
        for i, service in enumerate(self.services):
            if not service.is_available():
                continue

            try:
                logger.info(
                    f"Attempting translation with service {i + 1}/{len(self.services)}"
                )
                result = await service.translate(text, target_language, source_language)
                if result:
                    logger.info(f"Translation successful with service {i + 1}")
                    return result
                else:
                    logger.warning(f"Service {i + 1} returned empty result")
            except Exception as e:
                logger.error(f"Service {i + 1} failed: {e}")
                continue

        logger.error("All translation services failed")
        return None

    def get_available_services(self) -> list[str]:
        """Get list of available service names.

        Returns:
            List of service class names
        """
        return [
            service.__class__.__name__
            for service in self.services
            if service.is_available()
        ]
