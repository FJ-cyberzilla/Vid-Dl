import pytest
from sota_dl.infrastructure.adapters.cookies.factory import get_cookie_adapter
from sota_dl.infrastructure.errors import BrowserNotSupportedError


def test_get_cookie_adapter_success() -> None:
    get_cookie_adapter("chrome")
    get_cookie_adapter("Firefox")
    get_cookie_adapter("brave")
    get_cookie_adapter("netscape")


def test_get_cookie_adapter_failure() -> None:
    with pytest.raises(BrowserNotSupportedError):
        get_cookie_adapter("edge")
    with pytest.raises(BrowserNotSupportedError):
        get_cookie_adapter("unknown_browser")
