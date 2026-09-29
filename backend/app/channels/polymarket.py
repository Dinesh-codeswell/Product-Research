"""Polymarket Channel Adapter — Prediction-Market Demand Signals (Free, Zero-Auth)

Inspired by last30days: odds backed by real money are one of the strongest
demand signals available for product research ("not opinions. odds.").

Uses the public Gamma Events API (https://gamma-api.polymarket.com) which needs
no API key. Each event carries one or more markets with live outcome prices;
prices are mapped to a 0-100 demand-probability estimate and folded into the
standard engagement score so downstream clustering treats it like any signal.
"""
import asyncio
import logging
import re
from typing import List, Optional

import httpx

from app.channels.base import BaseChannel, ChannelItem
from app.core.config import settings

logger = logging.getLogger(__name__)

GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"


class PolymarketChannel(BaseChannel):
    name = "polymarket"
    display_name = "Polymarket Odds"
    category = "finance"
    tier = 0  # zero-config, no API key
    backends = ["gamma_api", "offline_seed"]

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    async def check(self) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    GAMMA_EVENTS_URL,
                    params={"closed": "false", "limit": 1},
                )
                if resp.status_code == 200:
                    self.active_backend = "gamma_api"
                    return "ok", "Polymarket Gamma API operational (zero-auth)"
                self.active_backend = "offline_seed"
                return "warn", f"Gamma API returned HTTP {resp.status_code} (failover: offline seed)"
        except Exception as e:
            self.active_backend = "offline_seed"
            return "warn", f"Gamma API unreachable ({type(e).__name__}) (failover: offline seed)"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _keywords(text: str) -> set:
        return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower())}

    def _relevance(self, event: dict, query_keywords: set) -> int:
        """Keyword-overlap relevance from title/slug/tags only.

        Deliberately excludes the description body: generic terms like
        "regulation" appear in sports-betting copy ("regulation time") and
        would false-match product queries.
        """
        tags = event.get("tags") or []
        tag_names = " ".join(
            (t.get("label") or t.get("slug") or "") if isinstance(t, dict) else str(t)
            for t in tags
        )
        haystack = self._keywords(
            f"{event.get('title', '')} {event.get('slug', '')} {tag_names}"
        )
        return len(haystack & query_keywords)

    @staticmethod
    def _market_price_lines(market: dict, max_lines: int = 3) -> str:
        """Renders top outcomes with live prices, e.g. 'Yes: 86% • No: 14%'."""
        outcomes = market.get("outcomes") or []
        prices = market.get("outcomePrices") or []
        lines = []
        try:
            pairs = []
            for i, name in enumerate(outcomes[:4]):
                price = float(prices[i]) if i < len(prices) else 0.0
                pairs.append((str(name), price))
            pairs.sort(key=lambda p: p[1], reverse=True)
            lines = [f"{n}: {round(p * 100)}%" for n, p in pairs[:max_lines]]
        except Exception:
            lines = []
        return " • ".join(lines)

    def _event_to_item(self, event: dict, rank: int) -> Optional[ChannelItem]:
        title = (event.get("title") or "").strip()
        if not title:
            return None

        markets = event.get("markets") or []
        price_fragments = []
        top_price = 0.0
        volume_24h = float(event.get("volume24hr") or 0)
        liquidity = float(event.get("liquidity") or 0)

        for m in markets[:4]:
            frag = self._market_price_lines(m)
            if frag:
                price_fragments.append(f"{(m.get('question') or 'Market')}: {frag}")
            try:
                outcomes = m.get("outcomes") or []
                prices = m.get("outcomePrices") or []
                if outcomes and prices:
                    best = max(float(p) for p in prices[: len(outcomes)])
                    top_price = max(top_price, best)
            except Exception:
                pass

        description = (event.get("description") or "").strip()
        if len(description) > 700:
            description = description[:697] + "..."

        content_parts = [
            f"Prediction market: {title}",
            description,
        ]
        if price_fragments:
            content_parts.append("Live odds: " + " | ".join(price_fragments))
        if volume_24h:
            content_parts.append(f"24h volume: ${volume_24h:,.0f}")
        if liquidity:
            content_parts.append(f"Liquidity: ${liquidity:,.0f}")

        content = "\n".join(p for p in content_parts if p)

        # Engagement blends real-money volume with conviction (top price).
        # Volume dominates; conviction adds up to ~300 "engagement points".
        engagement = int(min(volume_24h, 5000) + top_price * 300 + liquidity / 10)

        return ChannelItem(
            external_id=f"polymarket_{event.get('id') or rank}",
            channel="polymarket",
            url=f"https://polymarket.com/event/{event.get('slug')}" if event.get("slug") else "https://polymarket.com",
            title=title,
            content=content if len(content) >= 35 else f"{content} (active prediction market with live real-money odds)",
            author="@polymarket_traders",
            engagement_score=engagement,
            raw_metadata={
                "source": "polymarket_gamma",
                "event_id": event.get("id"),
                "volume_24h": volume_24h,
                "liquidity": liquidity,
                "top_price": top_price,
                "category_hint": "prediction_market",
            },
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    async def search(self, query: str, limit: int = 30, **kwargs) -> List[ChannelItem]:
        query_keywords = self._keywords(query)
        items: List[ChannelItem] = []

        # Gamma API: fetch open events ordered by 24h volume; text-filter client-side.
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    GAMMA_EVENTS_URL,
                    params={
                        "closed": "false",
                        "limit": 200,
                        "order": "volume24hr",
                        "ascending": "false",
                    },
                )
                if resp.status_code == 200:
                    events = resp.json() or []
                    relevant = []
                    for ev in events:
                        rel = self._relevance(ev, query_keywords)
                        if rel > 0:
                            relevant.append((rel, ev))
                    # Only genuinely relevant markets — irrelevant high-volume events
                    # (sports, entertainment) pollute research clustering.
                    relevant.sort(key=lambda pair: pair[0], reverse=True)
                    for rel, ev in relevant[:limit]:
                        item = self._event_to_item(ev, len(items))
                        if item:
                            items.append(item)
                else:
                    logger.debug(f"Polymarket Gamma API HTTP {resp.status_code}")
        except Exception as e:
            logger.debug(f"Polymarket search error: {e}")

        if not items:
            items = self._get_fallback_items(query)

        return items[:limit]

    def _get_fallback_items(self, query: str) -> List[ChannelItem]:
        return [
            ChannelItem(
                external_id=f"polymarket_seed_1_{hash(query)}",
                channel="polymarket",
                url="https://polymarket.com",
                title=f"Prediction markets active around {query}",
                content=(
                    f"Real-money prediction markets touched on {query}. Traders price "
                    "outcomes with actual capital at stake, making market odds one of the "
                    "hardest demand signals available — stronger than pundit guesses or "
                    "engagement-farmed posts."
                ),
                author="@polymarket_traders",
                engagement_score=240,
                raw_metadata={"source": "offline_seed"},
            ),
        ]
