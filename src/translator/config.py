"""Configuration settings for the translation system."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    pass


class TranslationConfig(BaseSettings):
    """Configuration settings for translation services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI base URL"
    )
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", description="DeepSeek base URL"
    )
    google_translate_api_key: str = Field(
        default="", description="Google Translate API key"
    )

    # Translation Settings
    default_model: str = Field(
        default="deepseek-chat", description="Default translation model"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retries for API calls"
    )
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )
    batch_size: int = Field(
        default=10, description="Number of documents to process in parallel"
    )
    max_file_size_mb: float = Field(default=50.0, description="Maximum file size in MB")

    # Supported Languages
    supported_languages: list[str] = Field(
        default=[
            "en",  # English
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese (Simplified)
            "zh-tw",  # Chinese (Traditional)
            "vi",  # Vietnamese
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "ru",  # Russian
            "ar",  # Arabic
            "hi",  # Hindi
            "th",  # Thai
        ],
        description="List of supported language codes",
    )

    # File Format Support
    supported_extensions: list[str] = Field(
        default=[".txt", ".md", ".pdf", ".docx", ".doc", ".rtf"],
        description="Supported file extensions",
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="translation.log", description="Log file path")

    # Output Configuration
    output_directory: str = Field(
        default="translated", description="Output directory for translations"
    )
    preserve_structure: bool = Field(
        default=True, description="Preserve directory structure in output"
    )
    overwrite_existing: bool = Field(
        default=False, description="Overwrite existing translated files"
    )


class LanguageMapping(BaseModel):
    """Language code mapping for different translation services."""

    LANGUAGE_NAMES: dict[str, str] = {
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese (Simplified)",
        "zh-tw": "Chinese (Traditional)",
        "vi": "Vietnamese",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
    }

    GOOGLE_TRANSLATE_CODES: dict[str, str] = {
        "en": "en",
        "ja": "ja",
        "ko": "ko",
        "zh": "zh-cn",
        "zh-tw": "zh-tw",
        "vi": "vi",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "ru": "ru",
        "ar": "ar",
        "hi": "hi",
        "th": "th",
    }

    LANGDETECT_CODES: dict[str, str] = {
        "en": "en",
        "ja": "ja",
        "ko": "ko",
        "zh-cn": "zh",
        "zh-tw": "zh",
        "vi": "vi",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "ru": "ru",
        "ar": "ar",
        "hi": "hi",
        "th": "th",
    }


def get_config() -> TranslationConfig:
    """Get the global configuration instance."""
    return TranslationConfig()


def get_language_mapping() -> LanguageMapping:
    """Get the language mapping instance."""
    return LanguageMapping()
