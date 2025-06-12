#!/usr/bin/env python3
"""Quick setup script for the document translation system."""
# ruff: noqa: T201  # Allow print statements in setup script

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is supported."""
    if sys.version_info < (3, 12):
        print("❌ Python 3.12 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Set up environment file."""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_example.exists():
        print("❌ .env.example file not found")
        return False

    if env_file.exists():
        response = input("📁 .env file already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("⏭️  Keeping existing .env file")
            return True

    try:
        # Copy .env.example to .env
        with open(env_example) as src:
            content = src.read()

        with open(env_file, "w") as dst:
            dst.write(content)

        print("✅ Created .env file from template")
        print("📝 Please edit .env file and add your API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def test_basic_functionality():
    """Test basic system functionality."""
    print("\n🧪 Testing basic functionality...")

    try:
        # Add src to path
        sys.path.insert(0, str(Path("src")))

        # Test configuration
        from translator.config import get_config

        config = get_config()
        print(
            f"✅ Configuration loaded: {len(config.supported_languages)} languages supported"
        )

        # Test language detector
        from translator.language_detector import LanguageDetector

        detector = LanguageDetector()
        print("✅ Language detector initialized")

        # Test document loader
        from translator.document_loader import DocumentLoader

        loader = DocumentLoader()
        print("✅ Document loader initialized")

        # Test translation manager
        from translator.translation_service import TranslationManager

        manager = TranslationManager()
        available_services = manager.get_available_services()
        if available_services:
            print(f"✅ Translation services available: {', '.join(available_services)}")
        else:
            print("⚠️  No translation services configured (add API keys to .env)")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try installing dependencies first")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def show_next_steps():
    """Show next steps to the user."""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add at least one API key:")
    print("   - OPENAI_API_KEY for OpenAI/ChatGPT")
    print("   - DEEPSEEK_API_KEY for DeepSeek")
    print("   - GOOGLE_TRANSLATE_API_KEY for Google Translate")
    print()
    print("2. Test the system:")
    print("   python scripts/translate.py config-info")
    print()
    print("3. Try the examples:")
    print("   python examples/usage_examples.py")
    print()
    print("4. Translate your documents:")
    print("   python scripts/translate.py translate ./your_docs")
    print()
    print("📖 For more information, see TRANSLATION_README.md")


def main():
    """Main setup function."""
    print("🚀 Document Translation System Setup")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("\n💡 You can try installing dependencies manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Test functionality
    if not test_basic_functionality():
        print("\n💡 Basic functionality test failed.")
        print("   This might be normal if no API keys are configured yet.")

    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()
