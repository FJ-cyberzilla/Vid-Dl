from typing import Any
from unittest.mock import patch, MagicMock
from pathlib import Path
from sota_dl.ui.menu_renderer import (
    render_dashboard,
    render_settings_menu,
    get_menu_selection,
)
from sota_dl.core.models.system_status import SystemStatus


@patch("sota_dl.ui.menu_renderer.render_main_banner")
@patch("sota_dl.ui.menu_renderer.console.print")
def test_render_dashboard(
    mock_print: Any, mock_banner: MagicMock, tmp_path: Path
) -> None:
    status = SystemStatus(
        local_storage_path=tmp_path,
        cookies_path=tmp_path / "cookies",
        drm_mode="Remote",
        firebase_status="Configured",
        firebase_endpoint="https://test.endpoint",
    )
    render_dashboard(status)

    mock_banner.assert_called_once()
    assert mock_print.called


@patch("sota_dl.ui.menu_renderer.console.print")
def test_render_settings_menu(mock_print: Any, tmp_path: Path) -> None:
    render_settings_menu(tmp_path / "cookies", tmp_path / "downloads", 30, False)

    assert mock_print.called


@patch("sota_dl.ui.menu_renderer.Prompt.ask")
def test_get_menu_selection(mock_ask: MagicMock) -> None:
    mock_ask.return_value = "1"

    result = get_menu_selection("Select", ["1", "2"])

    assert result == "1"
    mock_ask.assert_called_once()
