# Document Translation System

A comprehensive Python-based document translation system that automatically detects document languages and translates them to multiple target languages using various translation APIs with fallback support.

## Features

- **Automatic Language Detection**: Uses `langdetect` to identify source document language
- **Multiple Translation Services**: Supports OpenAI/DeepSeek, Google Translate with automatic fallback
- **Batch Processing**: Efficient parallel processing of multiple documents
- **Multiple Document Formats**: TXT, MD, PDF, DOCX, DOC, RTF
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Flexible Output**: Preserve directory structure or flat output with language suffixes
- **Error Handling**: Robust retry mechanisms and detailed error reporting
- **CLI Interface**: Easy-to-use command-line interface with rich output

## Supported Languages

English (en), Japanese (ja), Korean (ko), Chinese Simplified (zh), Chinese Traditional (zh-tw), Vietnamese (vi), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Russian (ru), Arabic (ar), Hindi (hi), Thai (th)

## Installation

### Prerequisites

Python 3.12+ is required.

### Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually
pip install openai langdetect googletrans python-docx PyPDF2 aiofiles
pip install aiohttp tqdm loguru pydantic pydantic-settings click rich tenacity
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
# At minimum, you need one of these API keys:
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here  
GOOGLE_TRANSLATE_API_KEY=your_google_translate_api_key_here
```

## Usage

### Command Line Interface

#### Basic Translation
```bash
# Translate all documents in a directory to all supported languages
python scripts/translate.py translate ./docs

# Translate to specific languages only
python scripts/translate.py translate ./docs --languages en ja ko

# Specify custom output directory
python scripts/translate.py translate ./docs --output ./translations

# Overwrite existing translations
python scripts/translate.py translate ./docs --overwrite

# Process with custom batch size
python scripts/translate.py translate ./docs --batch-size 5
```

#### Utility Commands
```bash
# List all supported languages
python scripts/translate.py languages

# Check current configuration and available services
python scripts/translate.py config-info

# Detect language of a specific file
python scripts/translate.py detect-language ./docs/README.md

# Enable verbose logging
python scripts/translate.py -v translate ./docs

# Use custom log file
python scripts/translate.py --log-file custom.log translate ./docs
```

### Python API

```python
import asyncio
from pathlib import Path
from src.translator.processor import DocumentTranslator

async def main():
    translator = DocumentTranslator()
    
    # Translate directory
    results = await translator.translate_directory(
        source_directory=Path("./docs"),
        target_languages=["en", "ja", "ko"],
        output_directory=Path("./translated")
    )
    
    # Print summary
    translator.print_results_summary(results)

# Run the translation
asyncio.run(main())
```

### Individual Components

```python
# Language Detection
from src.translator.language_detector import LanguageDetector
from src.translator.document_loader import DocumentLoader

async def detect_language():
    loader = DocumentLoader()
    detector = LanguageDetector()
    
    content = await loader.load_document(Path("document.pdf"))
    language = detector.detect_language(content)
    print(f"Detected language: {language}")

# Translation Service
from src.translator.translation_service import TranslationManager

async def translate_text():
    manager = TranslationManager()
    result = await manager.translate(
        text="Hello, world!",
        target_language="ja",
        source_language="en"
    )
    print(f"Translation: {result}")
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_BASE_URL` | OpenAI base URL | https://api.openai.com/v1 |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - |
| `DEEPSEEK_BASE_URL` | DeepSeek base URL | https://api.deepseek.com |
| `GOOGLE_TRANSLATE_API_KEY` | Google Translate API key | - |
| `DEFAULT_MODEL` | Default translation model | deepseek-chat |
| `MAX_RETRIES` | Maximum retry attempts | 3 |
| `RETRY_DELAY` | Delay between retries (seconds) | 1.0 |
| `BATCH_SIZE` | Parallel processing batch size | 10 |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | 50.0 |
| `OUTPUT_DIRECTORY` | Default output directory | translated |
| `PRESERVE_STRUCTURE` | Preserve directory structure | true |
| `OVERWRITE_EXISTING` | Overwrite existing files | false |
| `LOG_LEVEL` | Logging level | INFO |

### File Format Support

- **Text Files**: `.txt`, `.md` (UTF-8 and Latin-1 encoding support)
- **PDF Files**: `.pdf` (text extraction using PyPDF2)
- **Word Documents**: `.docx`, `.doc` (requires python-docx)
- **Rich Text**: `.rtf` (basic RTF parsing)

## Translation Services

### 1. OpenAI/DeepSeek (Recommended)
- High-quality translations with context awareness
- Preserves formatting and structure
- Supports technical and creative content
- Rate limiting and retry support

### 2. Google Translate
- Fast and reliable for general content
- Good for batch processing
- Fallback option when AI services are unavailable

### Service Fallback
The system automatically tries services in order:
1. OpenAI (if configured)
2. DeepSeek (if configured separately)
3. Google Translate (if available)

## Output Structure

### Preserve Structure (Default)
```
translated/
├── en/
│   ├── folder1/
│   │   └── document1.md
│   └── document2.pdf
├── ja/
│   ├── folder1/
│   │   └── document1.md
│   └── document2.pdf
└── ko/
    ├── folder1/
    │   └── document1.md
    └── document2.pdf
```

### Flat Structure
```
translated/
├── document1_en.md
├── document1_ja.md  
├── document1_ko.md
├── document2_en.pdf
├── document2_ja.pdf
└── document2_ko.pdf
```

## Performance Tips

1. **Batch Size**: Adjust `--batch-size` based on your system and API limits
2. **File Size**: Large files are automatically skipped (configurable limit)
3. **Caching**: Enable `OVERWRITE_EXISTING=false` to skip existing translations
4. **Logging**: Use appropriate log levels to balance detail and performance
5. **API Limits**: Configure retry settings for your API rate limits

## Error Handling

- **API Failures**: Automatic retry with exponential backoff
- **File Errors**: Detailed logging with file-specific error messages
- **Language Detection**: Falls back to service auto-detection
- **Encoding Issues**: Multiple encoding attempts for text files
- **Service Unavailable**: Automatic fallback to alternative services

## Troubleshooting

### Common Issues

1. **No translation services configured**
   ```bash
   python scripts/translate.py config-info
   ```
   Check that at least one API key is configured.

2. **Import errors**
   ```bash
   pip install -r requirements.txt
   ```
   Ensure all dependencies are installed.

3. **File not supported**
   Check the file extension is in the supported list and file size is under the limit.

4. **API rate limits**
   Reduce batch size or increase retry delay:
   ```bash
   python scripts/translate.py translate ./docs --batch-size 1
   ```

5. **Memory issues with large files**
   Reduce `MAX_FILE_SIZE_MB` in configuration or process files individually.

### Debug Mode

Enable verbose logging for detailed troubleshooting:
```bash
python scripts/translate.py -v translate ./docs
```

## Development

### Project Structure
```
src/translator/
├── __init__.py
├── config.py              # Configuration management
├── document_loader.py     # Document loading and parsing
├── language_detector.py   # Language detection
├── translation_service.py # Translation service implementations
├── processor.py           # Main translation processor
└── cli.py                 # Command-line interface
```

### Adding New Translation Services

1. Create a new service class inheriting from `TranslationService`
2. Implement `translate()` and `is_available()` methods
3. Add the service to `TranslationManager._setup_services()`

### Adding New Document Formats

1. Add the extension to `supported_extensions` in config
2. Implement a new `_load_*_file()` method in `DocumentLoader`
3. Add the format to the loader's `load_document()` method

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information
