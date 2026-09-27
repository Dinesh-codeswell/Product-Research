"""PulseRadar Multi-Channel Registry & Diagnostic Doctor Engine"""
import asyncio
from typing import Dict, List, Optional, Any
from app.channels.base import BaseChannel, ChannelItem
from app.channels.google import GoogleChannel
from app.channels.reddit import RedditChannel
from app.channels.youtube import YouTubeChannel
from app.channels.twitter import TwitterChannel
from app.channels.hackernews import HackerNewsChannel
from app.channels.github import GitHubChannel
from app.channels.facebook import FacebookChannel
from app.channels.v2ex import V2EXChannel
from app.channels.web import WebChannel
from app.channels.xueqiu import XueqiuChannel
from app.channels.bilibili import BilibiliChannel
from app.channels.linkedin import LinkedInChannel
from app.channels.exa import ExaChannel

CHANNEL_REGISTRY: Dict[str, BaseChannel] = {
    "google": GoogleChannel(),
    "reddit": RedditChannel(),
    "youtube": YouTubeChannel(),
    "twitter": TwitterChannel(),
    "hackernews": HackerNewsChannel(),
    "github": GitHubChannel(),
    "facebook": FacebookChannel(),
    "v2ex": V2EXChannel(),
    "web": WebChannel(),
    "xueqiu": XueqiuChannel(),
    "bilibili": BilibiliChannel(),
    "linkedin": LinkedInChannel(),
    "exa": ExaChannel(),
}

def get_channel(name: str) -> Optional[BaseChannel]:
    """Retrieve channel instance by unique identifier or alias."""
    name_clean = name.strip().lower()
    if name_clean in CHANNEL_REGISTRY:
        return CHANNEL_REGISTRY[name_clean]
    if name_clean in ["jina", "jina_reader"]:
        return CHANNEL_REGISTRY["web"]
    if name_clean in ["hn"]:
        return CHANNEL_REGISTRY["hackernews"]
    if name_clean in ["x"]:
        return CHANNEL_REGISTRY["twitter"]
    return None

def get_all_channels() -> List[BaseChannel]:
    return list(CHANNEL_REGISTRY.values())

async def run_channel_doctor() -> Dict[str, Any]:
    """
    Run non-destructive diagnostic health checks across all registered channels concurrently.
    Returns status, category, tier, active backend, and latency/diagnostic notes.
    """
    results: Dict[str, Any] = {}
    channel_items = list(CHANNEL_REGISTRY.items())

    async def probe_single(name: str, ch: BaseChannel):
        try:
            status, message = await asyncio.wait_for(ch.check(), timeout=8.0)
            active = getattr(ch, "active_backend", None) or (ch.backends[0] if ch.backends else "builtin")
            return name, {
                "id": name,
                "display_name": ch.display_name,
                "category": ch.category,
                "tier": ch.tier,
                "status": status,
                "message": message,
                "backends": ch.backends,
                "active_backend": active
            }
        except asyncio.TimeoutError:
            return name, {
                "id": name,
                "display_name": ch.display_name,
                "category": ch.category,
                "tier": ch.tier,
                "status": "warn",
                "message": "Probe timed out (upstream server high latency)",
                "backends": ch.backends,
                "active_backend": getattr(ch, "active_backend", None)
            }
        except Exception as e:
            return name, {
                "id": name,
                "display_name": ch.display_name,
                "category": ch.category,
                "tier": ch.tier,
                "status": "error",
                "message": f"Diagnostic check exception: {str(e)}",
                "backends": ch.backends,
                "active_backend": None
            }

    probe_tasks = [probe_single(name, ch) for name, ch in channel_items]
    outcomes = await asyncio.gather(*probe_tasks)

    for name, data in outcomes:
        results[name] = data

    ok_count = sum(1 for d in results.values() if d["status"] == "ok")
    warn_count = sum(1 for d in results.values() if d["status"] == "warn")
    error_count = sum(1 for d in results.values() if d["status"] == "error")

    return {
        "total_channels": len(results),
        "ok_channels": ok_count,
        "warn_channels": warn_count,
        "error_channels": error_count,
        "channels": results
    }

__all__ = [
    "BaseChannel",
    "ChannelItem",
    "CHANNEL_REGISTRY",
    "get_channel",
    "get_all_channels",
    "run_channel_doctor"
]
