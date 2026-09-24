"""Tests for LiveBrowserAgent"""
import pytest
import asyncio
from app.browser_agent.agent import LiveBrowserAgent

@pytest.mark.anyio
async def test_browser_agent_detection_and_sweep():
    agent = LiveBrowserAgent()
    assert agent is not None

    events = []
    def record_event(sid, stage, pct, msg, data=None):
        events.append({"stage": stage, "percent": pct, "message": msg, "data": data})

    items = await agent.run_live_browser_sweep(
        session_id="test_browser_session_1",
        query="Supabase latency",
        channels=["hackernews"],
        max_items=5,
        event_publisher=record_event
    )

    assert len(items) > 0
    assert any(it.channel == "hackernews" for it in items)
    assert len(events) >= 2
    # Verify at least one event has action metadata
    assert any("action" in (e.get("data") or {}) for e in events)

@pytest.mark.anyio
async def test_browser_agent_reddit_and_twitter_sweep():
    agent = LiveBrowserAgent()
    events = []
    def record_event(sid, stage, pct, msg, data=None):
        events.append(data)

    items = await agent.run_live_browser_sweep(
        session_id="test_browser_session_multi",
        query="Next.js App Router performance",
        channels=["reddit", "twitter"],
        max_items=6,
        event_publisher=record_event
    )

    assert len(items) >= 2
    channels_found = {it.channel for it in items}
    assert "reddit" in channels_found or "twitter" in channels_found
    for it in items:
        assert len(it.content) > 15
        assert it.url.startswith("http")
