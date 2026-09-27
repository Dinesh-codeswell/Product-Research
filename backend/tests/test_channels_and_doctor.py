"""Tests for Multi-Channel Adapters & Diagnostic Doctor Engine"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.channels import get_channel, get_all_channels, run_channel_doctor
from app.channels.v2ex import V2EXChannel
from app.channels.web import WebChannel
from app.channels.xueqiu import XueqiuChannel
from app.channels.bilibili import BilibiliChannel
from app.channels.linkedin import LinkedInChannel
from app.channels.exa import ExaChannel

@pytest.mark.anyio
async def test_channel_registry():
    channels = get_all_channels()
    assert len(channels) >= 13

    for ch_name in ["google", "reddit", "youtube", "twitter", "hackernews", "github", "facebook", "v2ex", "web", "xueqiu", "bilibili", "linkedin", "exa"]:
        ch = get_channel(ch_name)
        assert ch is not None
        assert ch.name == ch_name
        assert ch.display_name != ""
        assert ch.category in ["developer", "social", "video", "web", "business", "finance"]
        assert ch.tier in [0, 1, 2]

@pytest.mark.anyio
async def test_doctor_diagnostics():
    report = await run_channel_doctor()
    assert "total_channels" in report
    assert report["total_channels"] >= 13
    assert "channels" in report

    for name in ["v2ex", "web", "hackernews", "youtube", "github"]:
        assert name in report["channels"]
        ch_info = report["channels"][name]
        assert ch_info["status"] in ["ok", "warn", "error"]
        assert ch_info["message"] != ""

@pytest.mark.anyio
async def test_v2ex_channel_mock_or_live():
    ch = V2EXChannel()
    # Test checking
    status, msg = await ch.check()
    assert status in ["ok", "warn"]

@pytest.mark.anyio
async def test_web_jina_reader():
    # Test Jina reader on example.com
    md = await WebChannel.read_url_markdown("https://example.com", timeout=10.0)
    if md:
        assert "Example Domain" in md

@pytest.mark.anyio
async def test_api_doctor_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/doctor")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_channels" in data
        assert data["total_channels"] >= 13
        assert "v2ex" in data["channels"]
        assert "web" in data["channels"]
        assert "bilibili" in data["channels"]
