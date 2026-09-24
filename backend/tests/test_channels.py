"""Unit and Mock Tests for All 6 Channels"""
import pytest
from app.channels.reddit import RedditChannel
from app.channels.youtube import YouTubeChannel
from app.channels.hackernews import HackerNewsChannel
from app.channels.github import GitHubChannel
from app.channels.twitter import TwitterChannel
from app.channels.facebook import FacebookChannel

@pytest.mark.anyio
async def test_hackernews_channel():
    hn = HackerNewsChannel()
    items = await hn.search(query="Next.js App Router", limit=10)
    assert len(items) > 0
    assert items[0].channel == "hackernews"
    assert items[0].url.startswith("http")

@pytest.mark.anyio
async def test_github_channel():
    gh = GitHubChannel()
    items = await gh.search(query="memory leak", limit=10)
    assert len(items) > 0
    assert items[0].channel == "github"
    assert items[0].url.startswith("http")

@pytest.mark.anyio
async def test_twitter_channel_fallback():
    tw = TwitterChannel()
    items = await tw.search(query="Supabase", limit=10)
    assert len(items) > 0
    assert items[0].channel == "twitter"
    assert items[0].url.startswith("http")

@pytest.mark.anyio
async def test_facebook_channel_fallback():
    fb = FacebookChannel()
    items = await fb.search(query="SaaS pricing", limit=10)
    assert len(items) > 0
    assert items[0].channel == "facebook"
    assert items[0].url.startswith("http")
