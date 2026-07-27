from unittest.mock import patch
from ui.prompts import get_audio_quality, get_video_quality, get_quality_choice


@patch("ui.prompts.Prompt.ask")
@patch("ui.prompts.console.print")
def test_get_audio_quality(mock_print, mock_ask):
    mock_ask.return_value = "1"
    assert get_audio_quality() == "320"
    mock_ask.assert_called_once()
    assert mock_print.called


@patch("ui.prompts.Prompt.ask")
@patch("ui.prompts.console.print")
def test_get_video_quality(mock_print, mock_ask):
    mock_ask.return_value = "2"
    assert get_video_quality() == "720"
    mock_ask.assert_called_once()
    assert mock_print.called


@patch("ui.prompts.get_audio_quality")
@patch("ui.prompts.get_video_quality")
@patch("ui.prompts.console.print")
def test_get_quality_choice_audio(mock_print, mock_video, mock_audio):
    mock_audio.return_value = "320"
    assert get_quality_choice(True) == "320"
    mock_audio.assert_called_once()
    mock_video.assert_not_called()
    assert mock_print.called


@patch("ui.prompts.get_audio_quality")
@patch("ui.prompts.get_video_quality")
@patch("ui.prompts.console.print")
def test_get_quality_choice_video(mock_print, mock_video, mock_audio):
    mock_video.return_value = "720"
    assert get_quality_choice(False) == "720"
    mock_video.assert_called_once()
    mock_audio.assert_not_called()
    assert mock_print.called
