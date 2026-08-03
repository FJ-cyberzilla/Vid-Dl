import pytest
from pathlib import Path
from sota_dl.core.target_resolver import TargetResolver


def test_resolve_single_url() -> None:
    targets = TargetResolver.resolve("https://example.com")
    assert targets == ["https://example.com"]


def test_resolve_batch_file(tmp_path: Path) -> None:
    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://a.com\n#comment\n\nhttps://b.com")

    targets = TargetResolver.resolve(str(batch_file))
    assert targets == ["https://a.com", "https://b.com"]


def test_empty_batch_file_raises(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    with pytest.raises(ValueError, match="no valid URLs"):
        TargetResolver.resolve(str(empty_file))
