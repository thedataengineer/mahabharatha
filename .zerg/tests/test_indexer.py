"""Tests for ZERG v2 Index Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSymbol:
    """Tests for Symbol dataclass."""

    def test_symbol_creation(self):
        """Test Symbol can be created."""
        from indexer import Symbol

        symbol = Symbol(name="my_func", symbol_type="function", line=10)
        assert symbol.name == "my_func"
        assert symbol.symbol_type == "function"
        assert symbol.line == 10

    def test_symbol_to_dict(self):
        """Test Symbol serialization."""
        from indexer import Symbol

        symbol = Symbol(name="MyClass", symbol_type="class", line=5, doc="A class")
        data = symbol.to_dict()
        assert data["name"] == "MyClass"
        assert data["type"] == "class"
        assert data["line"] == 5


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test FileInfo can be created."""
        from indexer import FileInfo

        info = FileInfo(path="src/main.py", language="python")
        assert info.path == "src/main.py"
        assert info.language == "python"

    def test_file_info_with_symbols(self):
        """Test FileInfo with symbols."""
        from indexer import FileInfo, Symbol

        symbols = [Symbol(name="foo", symbol_type="function", line=1)]
        info = FileInfo(path="test.py", language="python", symbols=symbols)
        assert len(info.symbols) == 1


class TestLanguageDetector:
    """Tests for LanguageDetector."""

    def test_detect_python(self):
        """Test detecting Python files."""
        from indexer import LanguageDetector

        detector = LanguageDetector()
        assert detector.detect("main.py") == "python"

    def test_detect_javascript(self):
        """Test detecting JavaScript files."""
        from indexer import LanguageDetector

        detector = LanguageDetector()
        assert detector.detect("app.js") == "javascript"

    def test_detect_typescript(self):
        """Test detecting TypeScript files."""
        from indexer import LanguageDetector

        detector = LanguageDetector()
        assert detector.detect("index.ts") == "typescript"

    def test_detect_unknown(self):
        """Test detecting unknown file types."""
        from indexer import LanguageDetector

        detector = LanguageDetector()
        assert detector.detect("README.md") == "unknown"


class TestSymbolExtractor:
    """Tests for SymbolExtractor."""

    def test_extract_python_function(self):
        """Test extracting Python function."""
        from indexer import SymbolExtractor

        extractor = SymbolExtractor()
        content = "def my_function():\n    pass"
        symbols = extractor.extract(content, "python")
        assert len(symbols) == 1
        assert symbols[0].name == "my_function"
        assert symbols[0].symbol_type == "function"

    def test_extract_python_class(self):
        """Test extracting Python class."""
        from indexer import SymbolExtractor

        extractor = SymbolExtractor()
        content = "class MyClass:\n    pass"
        symbols = extractor.extract(content, "python")
        assert len(symbols) == 1
        assert symbols[0].name == "MyClass"
        assert symbols[0].symbol_type == "class"

    def test_extract_multiple_symbols(self):
        """Test extracting multiple symbols."""
        from indexer import SymbolExtractor

        extractor = SymbolExtractor()
        content = "def foo():\n    pass\n\nclass Bar:\n    pass"
        symbols = extractor.extract(content, "python")
        assert len(symbols) == 2


class TestIndexer:
    """Tests for Indexer."""

    def test_indexer_creation(self):
        """Test Indexer can be created."""
        from indexer import Indexer

        indexer = Indexer()
        assert indexer is not None

    def test_indexer_with_config(self):
        """Test Indexer with config."""
        from indexer import IndexConfig, Indexer

        config = IndexConfig(format="json", embeddings=True)
        indexer = Indexer(config=config)
        assert indexer.config.embeddings is True


class TestIndexCommand:
    """Tests for IndexCommand."""

    def test_command_creation(self):
        """Test IndexCommand can be created."""
        from indexer import IndexCommand

        cmd = IndexCommand()
        assert cmd is not None

    def test_command_dry_run(self):
        """Test dry run returns empty index."""
        from indexer import IndexCommand

        cmd = IndexCommand()
        result = cmd.run(path=".", dry_run=True)
        assert len(result.files) == 0
