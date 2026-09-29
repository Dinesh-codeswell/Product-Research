"""Discovery Engine — Velocity-Ranked Topic Discovery (last30days pattern)

Instead of researching a topic you already know, discovery answers:
"what's exploding in <category>?" It sweeps high-velocity sources
(HN front page, arXiv new listings, Polymarket high-volume markets,
Techmeme river), scores each candidate topic by cross-source momentum,
and returns 5-10 momentum-ranked topic suggestions — each pre-resolved
into a ready-to-run PulseRadar research query.
"""
import asyncio
import logging
import re
from collections import Counter
from typing import Dict, Any, List, Optional

from app.channels import CHANNEL_REGISTRY

logger = logging.getLogger(__name__)

# Sources that expose "what's hot right now" without needing a query
DISCOVERY_SOURCES = ["hackernews", "arxiv", "polymarket", "techmeme"]

# Generic/seed noise to suppress from topic candidates
STOP_TOPICS = {
    "ask hn", "show hn", "tell hn", "launch hn", "hiring", "who is hiring",
    "freelancer", "seeking feedback", "job", "careers",
}


class DiscoveryEngine:
    def __init__(self, max_items_per_source: int = 40):
        self.max_items_per_source = max_items_per_source

    # ------------------------------------------------------------------
    async def _sweep_source(self, channel_name: str) -> List[Any]:
        """Sweeps a discovery source using a broad neutral probe query."""
        channel = CHANNEL_REGISTRY.get(channel_name)
        if not channel:
            return []
        try:
            # Channels are query-driven; discovery uses category probes
            probes = {
                "hackernews": "technology software",
                "arxiv": "machine learning",
                "polymarket": "politics economy technology",
                "techmeme": "technology",
            }
            return await channel.search(probes.get(channel_name, "technology"), limit=self.max_items_per_source)
        except Exception as e:
            logger.debug(f"Discovery sweep failed for {channel_name}: {e}")
            return []

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_topics(items: List[Any]) -> List[Dict[str, Any]]:
        """Extracts candidate topics (noun-ish bigrams/unigrams) from titles."""
        candidates: Counter = Counter()
        evidence: Dict[str, Dict[str, Any]] = {}

        for it in items:
            title = (it.title or "").strip()
            if not title or title.lower().startswith(tuple(STOP_TOPICS)):
                continue
            words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9+.-]{2,}", title)]
            # Unigrams worth surfacing: capitalized or tech-y tokens
            interesting_unigrams = [
                w for w in words
                if len(w) >= 4 and (w[0].isupper() or "." in w or "+" in w)
            ]
            # Bigrams: adjacent non-stopword pairs
            stop = {"the", "a", "an", "and", "or", "for", "with", "from", "into", "onto", "over", "after", "before", "why", "how", "what", "your", "its", "their", "this", "that", "new"}
            bigrams = [
                f"{words[i]} {words[i+1]}".lower()
                for i in range(len(words) - 1)
                if words[i].lower() not in stop and words[i+1].lower() not in stop
            ]

            local_terms = set()
            for term in [w.lower() for w in interesting_unigrams] + bigrams:
                local_terms.add(term)
            for term in local_terms:
                candidates[term] += 1
                ev = evidence.setdefault(term, {"channels": set(), "top_item": None, "top_engagement": 0})
                ev["channels"].add(it.channel)
                if it.engagement_score > ev["top_engagement"]:
                    ev["top_engagement"] = it.engagement_score
                    ev["top_item"] = it

        topics = []
        for term, count in candidates.most_common(40):
            if count < 2:
                continue  # need cross-item corroboration
            ev = evidence[term]
            platforms = ev["channels"]
            velocity = count * (1 + 0.5 * (len(platforms) - 1)) * (1 + min(ev["top_engagement"], 500) / 500)
            topics.append({
                "topic": term,
                "mentions": count,
                "platforms": sorted(platforms),
                "velocity_score": round(velocity, 1),
                "top_engagement": ev["top_engagement"],
                "example": (ev["top_item"].title or term)[:120] if ev["top_item"] else term,
            })

        topics.sort(key=lambda t: -t["velocity_score"])
        return topics

    # ------------------------------------------------------------------
    @staticmethod
    def _dedupe_topics(topics: List[Dict[str, Any]], max_topics: int = 8) -> List[Dict[str, Any]]:
        """Removes overlapping candidates (e.g. 'ai agents' vs 'agents ai')."""
        kept: List[Dict[str, Any]] = []
        kept_token_sets: List[set] = []

        def toks(t: str) -> set:
            return set(re.findall(r"[a-z0-9]{3,}", t.lower()))

        for t in topics:
            tt = toks(t["topic"])
            duplicate = False
            for kt in kept_token_sets:
                if not tt or not kt:
                    continue
                if tt == kt or (tt <= kt) or (kt <= tt) or len(tt & kt) / len(tt | kt) >= 0.6:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(t)
                kept_token_sets.append(tt)
            if len(kept) >= max_topics:
                break
        return kept

    # ------------------------------------------------------------------
    async def discover(self, category: Optional[str] = None, max_topics: int = 8) -> Dict[str, Any]:
        """Runs the parallel discovery sweep and returns ranked topic briefs."""
        sweeps = await asyncio.gather(*(self._sweep_source(s) for s in DISCOVERY_SOURCES))
        all_items = []
        for items in sweeps:
            all_items.extend(items)

        if category:
            cat_kw = {w for w in re.findall(r"[a-z0-9]{3,}", category.lower())}

            def cat_relevant(it: Any) -> bool:
                hay = f"{it.title or ''} {it.content or ''}".lower()
                return any(kw in hay for kw in cat_kw)

            all_items = [it for it in all_items if cat_relevant(it)] or all_items

        topics = self._extract_topics(all_items)
        topics = self._dedupe_topics(topics, max_topics=max_topics)

        # Attach momentum labels
        for rank, t in enumerate(topics):
            t["momentum_label"] = "SURGING" if rank < max_topics // 3 else ("RISING" if rank < 2 * max_topics // 3 else "EMERGING")
            t["suggested_query"] = t["topic"].title()
            t["suggested_channels"] = (
                ["reddit", "youtube", "hackernews"]
                + (["polymarket"] if any(p in t["platforms"] for p in ("polymarket",)) else [])
                + (["arxiv"] if "arxiv" in t["platforms"] else [])
            )

        return {
            "success": True,
            "category": category or "general",
            "sources_swept": DISCOVERY_SOURCES,
            "signals_analyzed": len(all_items),
            "topics": topics,
            "note": (
                "Velocity-ranked from live multi-source sweeps: mentions are "
                "cross-item corroborated and weighted by platform diversity and "
                "engagement. Launch any topic as a research session with its "
                "suggested_query."
            ),
        }
