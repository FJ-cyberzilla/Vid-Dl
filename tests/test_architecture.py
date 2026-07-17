import unittest
from unittest.mock import MagicMock
from core.download_service import DownloadService
from core.protocols import Downloader

class TestDownloadService(unittest.TestCase):
    def setUp(self):
        self.mock_downloader = MagicMock(spec=Downloader)
        self.service = DownloadService(self.mock_downloader)

    def test_process_single_url(self):
        """Test that a single URL is passed correctly to the downloader."""
        target = "https://example.com/video"
        self.service.process_target(target)
        self.mock_downloader.execute.assert_called_once_with(target)

    def test_process_batch_file(self):
        """Test that a batch file is parsed and each URL is passed to the downloader."""
        # Create a temp batch file
        batch_file = "temp_batch.txt"
        urls = ["https://url1.com", "https://url2.com"]
        with open(batch_file, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
        
        try:
            self.service.process_target(batch_file)
            
            # Check if downloader was called for each URL
            self.assertEqual(self.mock_downloader.execute.call_count, 2)
            calls = [unittest.mock.call(url) for url in urls]
            self.mock_downloader.execute.assert_has_calls(calls)
        finally:
            import os
            if os.path.exists(batch_file):
                os.remove(batch_file)

    def test_process_empty_batch_file(self):
        """Test that an empty batch file raises an error."""
        batch_file = "empty_batch.txt"
        with open(batch_file, "w", encoding="utf-8") as f:
            f.write("")
        
        try:
            with self.assertRaises(ValueError):
                self.service.process_target(batch_file)
        finally:
            import os
            if os.path.exists(batch_file):
                os.remove(batch_file)

if __name__ == "__main__":
    unittest.main()
