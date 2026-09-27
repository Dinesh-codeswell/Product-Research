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
    assert res["stats"]["word_count"] > 50
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
    assert res["error"]


def test_chunk_transcript_into_signals_permalinks():
    """Chunking must preserve exact second-level deep links for evidence grounding."""
    transcript = {
        "video_id": "dQw4w9WgXcQ",
        "snippets": [
            {"text": "alpha " * 30, "start": 5.0, "duration": 2.0, "timestamp": "00:05",
             "permalink": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5s"},
            {"text": "beta " * 30, "start": 65.0, "duration": 2.0, "timestamp": "01:05",
             "permalink": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=65s"},
        ],
        "text": "alpha beta",
        "stats": {"duration_seconds": 70, "formatted_duration": "01:10", "snippets_count": 2, "word_count": 60},
    }
    chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(transcript, min_words_per_chunk=20, max_words_per_chunk=40)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk["video_id"] == "dQw4w9WgXcQ"
        assert chunk["permalink"] == f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&t={chunk['start_seconds']}s"
        assert chunk["formatted_time"] == format_seconds_to_timestamp(chunk["start_seconds"])
        assert chunk["word_count"] > 0


def test_chunk_transcript_handles_missing_snippets():
    assert YouTubeTranscriptEngine.chunk_transcript_into_signals({"video_id": "dQw4w9WgXcQ", "snippets": []}) == []
    assert YouTubeTranscriptEngine.chunk_transcript_into_signals({}) == []


def test_chunk_marks_chapter_cues_as_non_verbatim():
    """Chapter/description cues must never masquerade as verbatim spoken dialogue."""
    chapter_payload = {
        "video_id": "dQw4w9WgXcQ",
        "source": "video_chapters",
        "is_chapters_only": True,
        "snippets": [
            {"text": "Setup walkthrough and prerequisites for the demo", "start": 0.0, "duration": 60.0},
            {"text": "Deep dive into the authentication flow and edge cases", "start": 60.0, "duration": 60.0},
        ],
    }
    chapter_chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(
        chapter_payload, min_words_per_chunk=5, max_words_per_chunk=40
    )
    assert chapter_chunks, "chapter cues should still be chunkable for navigation"
    assert all(c["is_verbatim"] is False for c in chapter_chunks)
    assert all(c["source"] == "video_chapters" for c in chapter_chunks)

    subtitle_payload = dict(chapter_payload)
    subtitle_payload.update({"source": "youtube_subtitles", "is_chapters_only": False})
    subtitle_chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(
        subtitle_payload, min_words_per_chunk=5, max_words_per_chunk=40
    )
    assert subtitle_chunks
    assert all(c["is_verbatim"] is True for c in subtitle_chunks)


def test_video_id_extraction_from_timestamped_permalink():
    """Permalinks cited as evidence carry a &t=NNs offset the player must honour."""
    permalink = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=124s"
    assert extract_video_id(permalink) == "dQw4w9WgXcQ"
    assert extract_video_id("https://m.youtube.com/watch?v=_fthGXcfN34") == "_fthGXcfN34"


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
        assert all("&t=" in s["permalink"] for s in sig_data["signals"])


@pytest.mark.anyio
async def test_youtube_metadata_and_whisper_status_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 4. GET /api/v1/youtube/whisper-status (must never require a key to answer)
        status_resp = await ac.get("/api/v1/youtube/whisper-status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert set(["groq_configured", "openai_configured", "whisper_ready", "default_provider", "model"]).issubset(status.keys())
        assert isinstance(status["whisper_ready"], bool)

        # 5. GET /api/v1/youtube/info/{video_id} rejects malformed IDs cleanly
        bad_info = await ac.get("/api/v1/youtube/info/not-a-real-id")
        assert bad_info.status_code == 400


@pytest.mark.anyio
async def test_youtube_transcribe_endpoint_validates_input():
    """Whisper ASR endpoint must fail fast with a structured 400 for invalid videos."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/youtube/transcribe", json={"url_or_id": "not-a-real-id"})
        assert resp.status_code == 400
        assert "detail" in resp.json()


@pytest.mark.anyio
async def test_youtube_invalid_transcript_request_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/youtube/transcript", json={"url_or_id": "invalid_nonexistent_id_999"})
        assert resp.status_code == 400
        assert "detail" in resp.json()


@pytest.mark.anyio
async def test_youtube_channel_search():
    channel = YouTubeChannel()
    items = await channel.search("mechanical keyboard reviews", limit=6)
    assert len(items) > 0
    assert all(item.channel == "youtube" for item in items)
    assert all("youtube.com" in item.url for item in items)
