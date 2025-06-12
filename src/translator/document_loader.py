"""Document loading and parsing utilities."""

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from loguru import logger
from PyPDF2 import PdfReader

from .config import get_config

if TYPE_CHECKING:
    pass

try:
    from docx import Document as DocxDocument

    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    DocxDocument = None


class DocumentLoader:
    """Load and parse various document formats."""

    def __init__(self) -> None:
        """Initialize the document loader."""
        self.config = get_config()
        self.max_file_size_bytes = int(self.config.max_file_size_mb * 1024 * 1024)

    async def load_document(self, file_path: Path) -> str | None:
        """Load and extract text from a document.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content or None if failed
        """
        try:
            # Check file size
            if not self._validate_file_size(file_path):
                logger.warning(f"File {file_path} exceeds maximum size limit")
                return None

            # Check file extension
            extension = file_path.suffix.lower()
            if extension not in self.config.supported_extensions:
                logger.warning(f"Unsupported file extension: {extension}")
                return None

            # Load based on file type
            if extension in [".txt", ".md"]:
                return await self._load_text_file(file_path)
            elif extension == ".pdf":
                return await self._load_pdf_file(file_path)
            elif extension in [".docx", ".doc"]:
                return await self._load_docx_file(file_path)
            elif extension == ".rtf":
                return await self._load_rtf_file(file_path)
            else:
                logger.warning(f"No loader available for extension: {extension}")
                return None

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None

    def _validate_file_size(self, file_path: Path) -> bool:
        """Validate file size against maximum limit.

        Args:
            file_path: Path to the file

        Returns:
            True if file size is within limit
        """
        try:
            file_size = file_path.stat().st_size
            return file_size <= self.max_file_size_bytes
        except Exception as e:
            logger.error(f"Error checking file size for {file_path}: {e}")
            return False

    async def _load_text_file(self, file_path: Path) -> str | None:
        """Load content from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            File content as string
        """
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as file:
                content = await file.read()
                return content.strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                async with aiofiles.open(file_path, encoding="latin-1") as file:
                    content = await file.read()
                    return content.strip()
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return None

    async def _load_pdf_file(self, file_path: Path) -> str | None:
        """Load content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(str(file_path))
            text_content = []

            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_content.append(text.strip())

            return "\n\n".join(text_content) if text_content else None
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            return None

    async def _load_docx_file(self, file_path: Path) -> str | None:
        """Load content from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text content
        """
        if not HAS_DOCX:
            logger.error(
                "python-docx library not available. Install with: pip install python-docx"
            )
            return None

        try:
            doc = DocxDocument(str(file_path))
            text_content = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_content.append(text)

            return "\n\n".join(text_content) if text_content else None
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {e}")
            return None

    async def _load_rtf_file(self, file_path: Path) -> str | None:
        """Load content from an RTF file.

        Args:
            file_path: Path to the RTF file

        Returns:
            Extracted text content
        """
        try:
            # Basic RTF parsing - remove RTF formatting codes
            async with aiofiles.open(file_path, encoding="utf-8") as file:
                content = await file.read()

            # Simple RTF cleanup (basic implementation)
            lines = content.split("\\n")
            text_lines = []

            for line in lines:
                # Remove RTF control sequences
                clean_line = ""
                in_control = False

                for char in line:
                    if char == "\\":
                        in_control = True
                    elif char == " " and in_control:
                        in_control = False
                    elif not in_control:
                        clean_line += char

                clean_line = clean_line.strip()
                if (
                    clean_line
                    and not clean_line.startswith("{")
                    and not clean_line.startswith("}")
                ):
                    text_lines.append(clean_line)

            return "\n".join(text_lines) if text_lines else None
        except Exception as e:
            logger.error(f"Error reading RTF file {file_path}: {e}")
            return None

    async def get_supported_files(self, directory: Path) -> list[Path]:
        """Get all supported files from a directory recursively.

        Args:
            directory: Directory to scan

        Returns:
            List of supported file paths
        """
        supported_files = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    extension = file_path.suffix.lower()
                    if extension in self.config.supported_extensions:
                        if self._validate_file_size(file_path):
                            supported_files.append(file_path)
                        else:
                            logger.warning(f"Skipping {file_path}: file too large")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return supported_files
