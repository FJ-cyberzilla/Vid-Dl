from pathlib import Path
from utils.validators import is_valid_input, validate_options


def test_is_valid_input_http(tmp_path: Path) -> None:
    assert is_valid_input("https://example.com") is True
    assert is_valid_input("http://example.com") is True


def test_is_valid_input_batch_file(tmp_path: Path) -> None:
    batch_file = tmp_path / "list.txt"
    batch_file.write_text("http://example.com")
    assert is_valid_input(str(batch_file)) is True


def test_is_valid_input_invalid() -> None:
    assert is_valid_input("") is False
    assert is_valid_input("not-a-url") is False
    assert is_valid_input("file:///tmp/missing.txt") is False


def test_validate_options() -> None:
    class Opts:
        output_dir = "/home/test"
    assert validate_options(Opts()) is True
    assert validate_options(object()) is False
