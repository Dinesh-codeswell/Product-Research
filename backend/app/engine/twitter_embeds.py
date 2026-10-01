"""Twitter Embed Enrichment (FxEmbed-inspired)

Extracts rich embed data — images, videos, GIFs, poll results, and quoted
tweets — for X/Twitter status URLs, mirroring the payload shape of
FxTwitter / FixupX (github.com/FxEmbed/FxEmbed).

The public fx API (`https://api.fxtwitter.com/:user/status/:id`) is used when
reachable; every failure degrades silently so the research pipeline is never
blocked. Enriched data lands in `raw_metadata["embeds"]` and is rendered by
the frontend Evidence Drawer.
"""
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# fx API returns a normalised JSON payload for tweets (media, polls, quotes)
FX_API_BASE = "https://api.fxtwitter.com"
ENRICH_LIMIT = 12          # max tweets enriched per research sweep
REQUEST_TIMEOUT = 6.0      # never let embeds slow the pipeline

TWEET_URL_REGEX = re.compile(
    r"(?:https?://)?(?:www\.|mobile\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,15})/status/(\d+)",
    re.IGNORECASE,
)


def parse_tweet_url(url: str) -> Optional[Dict[str, str]]:
    """Extracts (screen_name, status_id) from any twitter.com / x.com status URL."""
    m = TWEET_URL_REGEX.search(url or "")
    if not m:
        return None
    return {"screen_name": m.group(1), "status_id": m.group(2)}


def extract_tweet_id(url: str) -> Optional[str]:
    parsed = parse_tweet_url(url)
    return parsed["status_id"] if parsed else None


async def fetch_embed_data(url: str) -> Optional[Dict[str, Any]]:
    """Fetches a normalised embed payload (media / poll / quote) for one tweet URL.

    Tries the v2 API first (`/2/status/:id` — full features: threads, polls,
    translations), then the legacy v1 path. Returns None on any failure —
    callers must treat embeds as best-effort.
    """
    parsed = parse_tweet_url(url)
    if not parsed:
        return None
    headers = {"User-Agent": "PulseRadar/1.0"}
    candidates = (
        f"{FX_API_BASE}/2/status/{parsed['status_id']}",
        f"{FX_API_BASE}/{parsed['screen_name']}/status/{parsed['status_id']}",
    )
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            for fx_url in candidates:
                try:
                    resp = await client.get(fx_url, headers=headers)
                    if resp.status_code != 200:
                        continue
                    body = resp.json() or {}
                    # v2 shape: {code, status: {...}} · v1 shape: {code, tweet: {...}}
                    tweet = body.get("tweet") or body.get("status") or {}
                    if tweet:
                        return _normalise(tweet, parsed)
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"FxEmbed candidate {fx_url} failed: {e}")
        return None
    except Exception as e:  # noqa: BLE001 — embeds must never break ingestion
        logger.debug(f"FxEmbed fetch failed for {url}: {e}")
        return None


def _normalise(tweet: Dict[str, Any], parsed: Dict[str, str]) -> Dict[str, Any]:
    """Reduces the fx payload (v1 'tweet' or v2 'status') to what PulseRadar renders."""
    author = tweet.get("author") or {}
    media: List[Dict[str, Any]] = []
    raw_media = tweet.get("media") or {}
    # v2: media.all[] · v1: media.all[] too, but tolerate photo/videos lists
    media_items = raw_media.get("all") if isinstance(raw_media, dict) else None
    if media_items is None and isinstance(raw_media, dict):
        media_items = (raw_media.get("photos") or []) + (raw_media.get("videos") or [])
    for m in media_items or []:
        mtype = m.get("type")
        if mtype == "video":
            videos = m.get("videos") or []
            duration = videos[0].get("durationMs") if videos else None
        else:
            duration = None
        media.append({
            "type": mtype,                       # photo | video | gif
            "url": m.get("url") or m.get("expandedUrl"),
            "thumbnail": m.get("thumbnailUrl") or (m.get("url") if mtype == "photo" else None),
            "alt": m.get("altText"),
            "duration_ms": duration,
        })

    poll = None
    raw_poll = tweet.get("poll")
    if raw_poll:
        total = raw_poll.get("total_votes") or 0
        poll = {
            "total_votes": total,
            "ends_at": raw_poll.get("ends_at"),
            "options": [
                {"label": o.get("label"), "votes": o.get("count") or 0,
                 "percent": round(100 * (o.get("count") or 0) / total, 1) if total else 0}
                for o in raw_poll.get("options", [])
            ],
        }

    quote = None
    raw_quote = tweet.get("quote")
    if raw_quote:
        q_author = raw_quote.get("author") or {}
        q_likes = raw_quote.get("likes")
        quote = {
            "author": q_author.get("screen_name") if isinstance(q_author, dict) else q_author,
            "text": raw_quote.get("text"),
            "url": raw_quote.get("url"),
            "likes": q_likes.get("count") if isinstance(q_likes, dict) else q_likes,
        }

    def _metric(key: str) -> Optional[int]:
        v = tweet.get(key)
        if isinstance(v, dict):                       # v1 shape: {count: N}
            v = v.get("count")
        return v if isinstance(v, (int, float)) else None

    screen_name = author.get("screen_name") or parsed["screen_name"]
    return {
        "provider": "fxembed",
        "screen_name": screen_name,
        "status_id": tweet.get("id") or parsed["status_id"],
        "likes": _metric("likes"),
        "retweets": _metric("reposts") or _metric("retweets"),
        "replies": _metric("replies"),
        "views": _metric("views"),
        "created_at": tweet.get("created_at") or tweet.get("created_timestamp"),
        "translated_text": (tweet.get("translation") or {}).get("text") if isinstance(tweet.get("translation"), dict) else None,
        "media": media,
        "poll": poll,
        "quote": quote,
    }


def engagement_from_embeds(embeds: Dict[str, Any]) -> Optional[int]:
    """Derives an engagement score from real fx metrics when available."""
    if not embeds:
        return None
    total = 0
    for key in ("likes", "retweets", "replies"):
        v = embeds.get(key)
        if isinstance(v, (int, float)):
            total += int(v)
    views = embeds.get("views")
    if isinstance(views, (int, float)):
        total += int(views) // 50   # 50 views ≈ 1 engagement unit
    return total or None


async def enrich_twitter_items(items: List[Any], limit: int = ENRICH_LIMIT) -> List[Any]:
    """Enriches ChannelItems produced by the Twitter channel in-place.

    Only status URLs are enriched; everything else passes through untouched.
    Real fx engagement metrics replace the crawler's randomised estimates.
    """
    enriched = 0
    for item in items:
        if enriched >= limit:
            break
        if not TWEET_URL_REGEX.search(item.url or ""):
            continue
        embeds = await fetch_embed_data(item.url)
        if embeds:
            item.raw_metadata = item.raw_metadata or {}
            item.raw_metadata["embeds"] = embeds
            real_score = engagement_from_embeds(embeds)
            if real_score:
                item.engagement_score = real_score
                item.raw_metadata["likes"] = embeds.get("likes") or item.raw_metadata.get("likes")
            enriched += 1
    if enriched:
        logger.info(f"FxEmbed enrichment: {enriched} tweets gained media/poll data")
    return items
