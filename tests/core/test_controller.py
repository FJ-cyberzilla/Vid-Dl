import pytest
import threading
from sota_dl.core.controller import DownloadController
from sota_dl.core.protocols import DownloadStatus


@pytest.fixture
def controller() -> DownloadController:
    return DownloadController()


@pytest.mark.parametrize(
    "action, expected_status, expected_cancelled, expected_pause_set",
    [
        ("reset", DownloadStatus.DOWNLOADING, False, True),
        ("pause", DownloadStatus.PAUSED, False, False),
        ("resume", DownloadStatus.DOWNLOADING, False, True),
        ("cancel", DownloadStatus.CANCELLED, True, True),
    ],
)
def test_controller_actions(
    controller: DownloadController,
    action: str,
    expected_status: DownloadStatus,
    expected_cancelled: bool,
    expected_pause_set: bool,
) -> None:
    """Test individual controller actions."""
    if action == "reset":
        controller.reset()
    elif action == "pause":
        controller.pause()
    elif action == "resume":
        controller.resume()
    elif action == "cancel":
        controller.cancel()

    assert controller.status == expected_status
    assert controller.cancelled == expected_cancelled
    assert controller.pause_event.is_set() == expected_pause_set


def test_check_state_not_cancelled(controller: DownloadController) -> None:
    controller.check_state()  # Should not raise


def test_check_state_cancelled(controller: DownloadController) -> None:
    controller.cancel()
    with pytest.raises(Exception, match="Download cancelled"):
        controller.check_state()


def test_check_state_paused_then_resumed(controller: DownloadController) -> None:
    controller.pause()

    # Use thread to resume after a short delay
    def resume_after_delay() -> None:
        import time

        time.sleep(0.1)
        controller.resume()

    threading.Thread(target=resume_after_delay, daemon=True).start()

    controller.check_state()  # Should block then succeed
