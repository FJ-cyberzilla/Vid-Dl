from typing import Any
import pytest
from unittest.mock import patch, MagicMock
from sota_dl.ui.menus import launch_command_center


@patch("sota_dl.ui.menus.check_ffmpeg", return_value=True)
@patch("sota_dl.ui.menus.menu_renderer.Prompt.ask")
@patch("sota_dl.ui.menus.menu_renderer.render_dashboard")
def test_launch_command_center_termination(
    mock_render: Any, mock_prompt: MagicMock, mock_check_ffmpeg: Any
) -> None:
    # Setup mock to terminate immediately
    mock_prompt.return_value = "4"

    with pytest.raises(SystemExit) as e:
        launch_command_center()

    assert e.value.code == 0
