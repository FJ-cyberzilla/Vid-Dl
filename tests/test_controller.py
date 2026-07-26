import pytest
import threading
from core.controller import DownloadController
from core.protocols import DownloadStatus


def test_controller_state_transitions() -> None:
    controller: DownloadController = DownloadController()

    # Test reset
    controller.reset()
    assert controller.status is DownloadStatus.DOWNLOADING
    assert not controller.cancelled
    assert controller.pause_event.is_set()

    # Test pause
    controller.pause()
    assert controller.status is DownloadStatus.PAUSED  # type: ignore[comparison-overlap]
    assert not controller.pause_event.is_set()

    # Test resume
    controller.resume()
    assert controller.status is DownloadStatus.DOWNLOADING
    assert controller.pause_event.is_set()

    # Test cancel
    controller.cancel()
    assert controller.status == DownloadStatus.CANCELLED
    assert controller.cancelled
    assert controller.pause_event.is_set()


def test_check_state_not_cancelled() -> None:
    controller = DownloadController()
    controller.check_state()  # Should not raise


def test_check_state_cancelled() -> None:
    controller = DownloadController()
    controller.cancel()
    with pytest.raises(Exception, match="Download cancelled"):
        controller.check_state()


def test_check_state_paused_then_resumed() -> None:
    controller = DownloadController()
    controller.pause()

    # Use thread to resume after a short delay
    def resume_after_delay() -> None:
        import time

        time.sleep(0.1)
        controller.resume()

    threading.Thread(target=resume_after_delay, daemon=True).start()

    controller.check_state()  # Should block then succeed
