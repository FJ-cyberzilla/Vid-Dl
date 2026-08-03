import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from sota_dl.infrastructure.adapters.browser_cookies import BrowserCookieAdapter


def test_get_cookies_for_url_dynamic_success() -> None:
    with patch("browser_cookie3.chrome") as mock_chrome:
        cookie1 = MagicMock()
        cookie1.name = "cookie1"
        cookie1.value = "value1"
        cookie2 = MagicMock()
        cookie2.name = "cookie2"
        cookie2.value = "value2"
        mock_cj = [cookie1, cookie2]
        mock_chrome.return_value = mock_cj

        adapter = BrowserCookieAdapter()
        cookies = adapter.get_cookies_for_url("https://example.com")

        assert cookies == {"cookie1": "value1", "cookie2": "value2"}
        # Expect 'example.com' instead of 'https://example.com'
        mock_chrome.assert_called_once_with(domain_name="example.com")


def test_get_cookies_for_url_dynamic_failure_fallback_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Create cookie file
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "example.com\tTRUE\t/\tFALSE\t0\tname1\tvalue1\nexample.com\tTRUE\t/\tFALSE\t0\tname2\tvalue2",
        encoding="utf-8",
    )

    # Patch COOKIES_PATH to point to our temp file
    monkeypatch.setattr(
        "sota_dl.infrastructure.adapters.browser_cookies.COOKIES_PATH", cookie_file
    )

    with patch("browser_cookie3.chrome") as mock_chrome:
        mock_chrome.side_effect = Exception("Browser error")

        adapter = BrowserCookieAdapter()
        # This should now trigger _extract_from_netscape_format
        cookies = adapter.get_cookies_for_url("https://example.com")

        assert cookies == {"name1": "value1", "name2": "value2"}


def test_load_cookies_from_file_valid(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "# Netscape format\nexample.com\tTRUE\t/\tFALSE\t0\tname1\tvalue1",
        encoding="utf-8",
    )

    adapter = BrowserCookieAdapter()
    cookies = adapter.load_cookies_from_file(cookie_file)
    assert cookies == {"name1": "value1"}


def test_load_cookies_from_file_invalid(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("invalid line", encoding="utf-8")

    adapter = BrowserCookieAdapter()
    cookies = adapter.load_cookies_from_file(cookie_file)
    assert cookies == {}
