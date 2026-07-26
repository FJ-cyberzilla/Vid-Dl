import unittest
import ast
import os
from unittest.mock import MagicMock
from core.download_service import DownloadService
from core.protocols import Downloader, DownloadOptions


class TestDownloadService(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_downloader = MagicMock(spec=Downloader)
        self.service = DownloadService(self.mock_downloader)

    def test_process_single_url(self) -> None:
        """Test that a single URL is passed correctly to the downloader."""
        target = "https://example.com/video"
        self.service.process_target(target)
        # Verify call included default options
        self.mock_downloader.execute.assert_called_once()
        args, _ = self.mock_downloader.execute.call_args
        self.assertEqual(args[0], target)
        self.assertIsInstance(args[1], DownloadOptions)

    def test_process_batch_file(self) -> None:
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
            for call_args in self.mock_downloader.execute.call_args_list:
                args, _ = call_args
                self.assertIn(args[0], urls)
                self.assertIsInstance(args[1], DownloadOptions)
        finally:
            import os

            if os.path.exists(batch_file):
                os.remove(batch_file)

    def test_process_empty_batch_file(self) -> None:
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


class TestLayerDependencies(unittest.TestCase):
    def test_core_does_not_import_infrastructure(self) -> None:
        """Enforce that core does not directly import from infrastructure."""
        core_dir = "core"
        for root, _, files in os.walk(core_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                if node.module and node.module.startswith(
                                    "infrastructure"
                                ):
                                    self.fail(
                                        f"Core module {file_path} illegally "
                                        f"imports from infrastructure: {node.module}"
                                    )
                            elif isinstance(node, ast.Import):
                                for alias in node.names:
                                    if alias.name.startswith("infrastructure"):
                                        self.fail(
                                            f"Core module {file_path} illegally "
                                            f"imports from infrastructure: {alias.name}"
                                        )


if __name__ == "__main__":
    unittest.main()
