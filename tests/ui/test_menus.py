import pytest
from unittest.mock import patch
from sota_dl.ui.menus import launch_command_center

# This is a very complex module, testing it will require significant mocking
# due to its tight coupling with console I/O and various services.
# This test is just to ensure the main menu can at least be initialized.


@patch("sota_dl.ui.menus.check_ffmpeg", return_value=True)
@patch("sota_dl.ui.menus.Prompt.ask")
@patch("sota_dl.ui.menus.menu_renderer.render_dashboard")
def test_launch_command_center_termination(mock_render, mock_prompt, mock_check_ffmpeg):
    # Setup mock to terminate immediately
    mock_prompt.return_value = "4"

    with pytest.raises(SystemExit) as e:
        launch_command_center()

    assert e.value.code == 0
