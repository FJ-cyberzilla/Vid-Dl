import pytest
from unittest.mock import MagicMock
from sota_dl.infrastructure.adapters.innertube import AndroidInnertubeAdapter

@pytest.fixture
def adapter():
    network_manager = MagicMock()
    return AndroidInnertubeAdapter(network_manager)

def test_extract_video_id_valid(adapter):
    assert adapter._extract_video_id("https://youtube.com/watch?v=12345678901") == "12345678901"
    assert adapter._extract_video_id("https://www.youtube.com/watch?v=12345678901") == "12345678901"
    assert adapter._extract_video_id("https://m.youtube.com/watch?v=12345678901") == "12345678901"
    assert adapter._extract_video_id("https://youtu.be/12345678901") == "12345678901"

def test_extract_video_id_invalid_domain(adapter):
    # Should not match
    assert adapter._extract_video_id("https://not-youtube.com/watch?v=12345678901") is None
    assert adapter._extract_video_id("https://evil.com/youtube.com/watch?v=12345678901") is None
    assert adapter._extract_video_id("https://youtube.com.attacker.com/watch?v=12345678901") is None
