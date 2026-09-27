"""Unit and integration tests for YouTube Transcript API and Channel Engine"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.engine.youtube_transcript import (
    extract_video_id,
    format_seconds_to_timestamp,
    YouTubeTranscriptEngine
)
from app.channels.youtube import YouTubeChannel


def test_extract_video_id():
    # Standard watch URL
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # With extra query parameters
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=shared") == "dQw4w9WgXcQ"
    # Short youtu.be URL
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Embed URL
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Shorts URL
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Raw 11-char ID
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Invalid URL
    assert extract_video_id("https://example.com/not-youtube") is None
    assert extract_video_id("") is None


def test_format_seconds_to_timestamp():
    assert format_seconds_to_timestamp(0) == "00:00"
    assert format_seconds_to_timestamp(45) == "00:45"
    assert format_seconds_to_timestamp(75) == "01:15"
    assert format_seconds_to_timestamp(3665) == "01:01:05"


def test_youtube_transcript_engine_real_video():
    """Test transcript retrieval on a widely available test video."""
    res = YouTubeTranscriptEngine.get_transcript("dQw4w9WgXcQ")
    assert res["success"] is True
    assert res["video_id"] == "dQw4w9WgXcQ"
    assert len(res["snippets"]) > 0
    assert res["stats"]["word_count"] > 100
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in res["video_url"]

    # Test signal chunking
    chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(res, min_words_per_chunk=30)
    assert len(chunks) > 0
    assert "t=" in chunks[0]["permalink"]
    assert chunks[0]["video_id"] == "dQw4w9WgXcQ"


def test_youtube_transcript_engine_invalid_video():
    res = YouTubeTranscriptEngine.get_transcript("invalid_nonexistent_id_999")
    assert res["success"] is False
    assert len(res["snippets"]) == 0


@pytest.mark.anyio
async def test_youtube_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. POST /api/v1/youtube/transcript
        resp = await ac.post("/api/v1/youtube/transcript", json={"url_or_id": "dQw4w9WgXcQ"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert len(data["snippets"]) > 0
        assert data["stats"]["snippets_count"] > 0

        # 2. GET /api/v1/youtube/transcript/{video_id}
        get_resp = await ac.get("/api/v1/youtube/transcript/dQw4w9WgXcQ")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["success"] is True

        # 3. POST /api/v1/youtube/signals
        sig_resp = await ac.post("/api/v1/youtube/signals", json={"url_or_id": "dQw4w9WgXcQ"})
        assert sig_resp.status_code == 200
        sig_data = sig_resp.json()
        assert sig_data["total_chunks"] > 0
        assert len(sig_data["signals"]) > 0


@pytest.mark.anyio
async def test_youtube_channel_search():
    channel = YouTubeChannel()
    items = await channel.search("mechanical keyboard reviews", limit=6)
    assert len(items) > 0
    assert all(item.channel == "youtube" for item in items)
    assert all("youtube.com" in item.url for item in items)
