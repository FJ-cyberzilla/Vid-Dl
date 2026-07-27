import pytest
import os
import ast
import threading
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock
from sota_dl.core.download_service import DownloadService
from sota_dl.core.protocols import Downloader, DownloadOptions


from sota_dl.core.controller import DownloadController

class TestDownloadService:
    def setup_method(self) -> None:
        self.mock_downloader = MagicMock(spec=Downloader)
        self.mock_controller = MagicMock(spec=DownloadController)
        # Configure default values
        self.mock_controller.cancelled = False
        self.mock_controller.pause_event = threading.Event()
        self.mock_controller.pause_event.set()
        
        self.service = DownloadService(
            downloader=self.mock_downloader, controller=self.mock_controller
        )

    def test_process_single_url(self) -> None:
        """Test that a single URL is passed correctly to the downloader."""
        target = "https://example.com/video"
        self.service.process_target(target)
        # Verify call included default options
        self.mock_downloader.execute.assert_called_once()
        args, _ = self.mock_downloader.execute.call_args
        assert args[0] == target
        assert isinstance(args[1], DownloadOptions)

    def test_process_batch_file(self, tmp_path: Path) -> None:
        """Test that a batch file is parsed and each URL is passed to the downloader."""
        # Create a temp batch file
        batch_file = tmp_path / "temp_batch.txt"
        urls = ["https://url1.com", "https://url2.com"]
        batch_file.write_text("\n".join(urls), encoding="utf-8")

        self.service.process_target(str(batch_file))

        # Check if downloader was called for each URL
        assert self.mock_downloader.execute.call_count == 2
        called_urls = [
            call_args.args[0]
            for call_args in self.mock_downloader.execute.call_args_list
        ]
        for url in urls:
            assert url in called_urls

    def test_process_empty_batch_file(self, tmp_path: Path) -> None:
        """Test that an empty batch file raises an error."""
        batch_file = tmp_path / "empty_batch.txt"
        batch_file.write_text("", encoding="utf-8")

        with pytest.raises(ValueError):
            self.service.process_target(str(batch_file))


def get_core_files() -> Generator[str, None, None]:
    core_dir = "core"
    for root, _, files in os.walk(core_dir):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


@pytest.mark.parametrize("file_path", list(get_core_files()))
def test_core_module_import_dependencies(file_path: str) -> None:
    """Enforce that core does not directly import from sota_dl.infrastructure."""
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("infrastructure"):
                    pytest.fail(
                        f"Core module {file_path} illegally "
                        f"imports from sota_dl.infrastructure: {node.module}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("infrastructure"):
                        pytest.fail(
                            f"Core module {file_path} illegally "
                            f"imports from sota_dl.infrastructure: {alias.name}"
                        )
