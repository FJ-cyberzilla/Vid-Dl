import unittest
from pathlib import Path
from utils.validators import is_valid_input
from config.settings import get_download_path


class TestSOTADownloader(unittest.TestCase):
    def test_is_valid_input_valid_urls(self) -> None:
        """Test is_valid_input with standard valid HTTP/HTTPS URLs."""
        valid_urls: list[str] = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://vimeo.com/81234567",
            "http://localhost:8000/media",
            "  https://youtube.com/watch?v=abcdef  ",  # leading/trailing spaces
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_valid_input(url))

    def test_is_valid_input_invalid_urls(self) -> None:
        """Test is_valid_input with invalid URLs."""
        invalid_urls: list[str | None] = [
            "ftp://invalid-url",
            "just_a_string",
            "http//missing-colon",
            "https://",
            "",
            None,
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                # Ensure we handle the None case explicitly for type checking
                input_str = url if url is not None else ""
                self.assertFalse(is_valid_input(input_str))

    def test_is_valid_input_batch_files(self) -> None:
        """Test is_valid_input with local .txt files."""
        # Create a temporary txt file
        temp_file = Path("test_batch_temp_file.txt")
        temp_file.write_text("https://example.com/video1\n", encoding="utf-8")

        try:
            self.assertTrue(is_valid_input(str(temp_file)))
            self.assertTrue(is_valid_input(f"  {temp_file}  "))  # with spaces
            # Test a non-existent txt file
            self.assertFalse(is_valid_input("non_existent_file.txt"))
            # Test a non-txt file
            self.assertFalse(is_valid_input("main.py"))
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_get_download_path(self) -> None:
        """Test that get_download_path returns a valid writeable directory."""
        path = get_download_path()
        self.assertIsNotNone(path)
        self.assertTrue(path.is_dir())
        # Ensure we have write access in the resolved path
        test_file = path / ".test_write_suite"
        try:
            test_file.write_text("test", encoding="utf-8")
            self.assertTrue(test_file.exists())
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    unittest.main()
