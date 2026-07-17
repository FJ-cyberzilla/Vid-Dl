import os
import unittest
from utils.validators import is_valid_input
from config.settings import get_download_path


class TestSOTADownloader(unittest.TestCase):
    def test_is_valid_input_valid_urls(self):
        """Test is_valid_input with standard valid HTTP/HTTPS URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://vimeo.com/81234567",
            "http://localhost:8000/media",
            "  https://youtube.com/watch?v=abcdef  "  # leading/trailing spaces
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_valid_input(url))

    def test_is_valid_input_invalid_urls(self):
        """Test is_valid_input with invalid URLs."""
        invalid_urls = [
            "ftp://invalid-url",
            "just_a_string",
            "http//missing-colon",
            "https://",
            "",
            None
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(is_valid_input(url))

    def test_is_valid_input_batch_files(self):
        """Test is_valid_input with local .txt files."""
        # Create a temporary txt file
        temp_file = "test_batch_temp_file.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("https://example.com/video1\n")

        try:
            self.assertTrue(is_valid_input(temp_file))
            self.assertTrue(is_valid_input(f"  {temp_file}  "))  # with spaces
            # Test a non-existent txt file
            self.assertFalse(is_valid_input("non_existent_file.txt"))
            # Test a non-txt file
            self.assertFalse(is_valid_input("main.py"))
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_get_download_path(self):
        """Test that get_download_path returns a valid writeable directory."""
        path = get_download_path()
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isdir(path))
        # Ensure we have write access in the resolved path
        test_file = os.path.join(path, ".test_write_suite")
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("test")
            self.assertTrue(os.path.exists(test_file))
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
