"""Engagement-Weighted Signal Scoring & Cross-Source Story Merging

Implements the last30days thesis: "Social relevancy, not SEO relevancy" —
a Reddit thread with 1,500 upvotes outweighs a blog post nobody read.

Two passes over harvested signals:
1. Momentum scoring: per-platform engagement normalization + recency decay
   + category weighting, producing a comparable 0-100 momentum score.
2. Cross-source cluster merging: duplicate stories appearing on multiple
   platforms (Reddit + HN + YouTube + Polymarket) merge into ONE cluster
   with multi-platform evidence instead of fragmenting into lookalikes.
"""
import logging
import math
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Tuple

from app.channels.base import ChannelItem

logger = logging.getLogger(__name__)

# Per-platform engagement normalization ceilings (log-scaled raw scores map to 0-1).
# Chosen from observed 95th-percentile values per platform.
PLATFORM_NORM = {
    "reddit": 900.0,        # score + num_comments
    "hackernews": 600.0,    # points + comments
    "youtube": 50_000.0,    # view counts
    "twitter": 4_000.0,
    "github": 900.0,
    "polymarket": 2_000.0,  # volume-derived engagement
    "arxiv": 200.0,
    "techmeme": 260.0,
    "hiring": 220.0,
    "facebook": 900.0,
    "v2ex": 300.0,
    "xueqiu": 1_500.0,
    "bilibili": 30_000.0,
    "linkedin": 900.0,
    "google": 300.0,
    "web": 300.0,
    "exa": 300.0,
}
DEFAULT_NORM = 500.0

# Platform credibility multipliers for cross-validation value
PLATFORM_WEIGHTS = {
    "reddit": 1.0,
    "hackernews": 1.0,
    "youtube": 0.9,
    "github": 0.95,
    "polymarket": 1.1,   # real-money signal
    "arxiv": 0.9,        # research signal
    "techmeme": 0.85,    # editorial signal
    "hiring": 1.05,      # revealed-preference signal
    "facebook": 0.8,
    "v2ex": 0.8,
    "xueqiu": 0.85,
    "bilibili": 0.8,
    "linkedin": 0.85,
    "google": 0.75,
    "web": 0.75,
    "exa": 0.75,
}

# Category momentum multipliers
CATEGORY_WEIGHTS = {
    "PAIN_POINT": 1.0,
    "CHURN_TRIGGER": 1.05,
    "WORKAROUND": 0.9,
    "DESIRE": 0.85,
}

# Momentum label thresholds
def momentum_label(score: float) -> str:
    if score >= 75:
        return "SURGING"
    if score >= 55:
        return "RISING"
    if score >= 35:
        return "STEADY"
    return "FADING"


class MomentumScorer:
    """Scores cleaned signals with normalized engagement + recency + credibility."""

    def __init__(self, now: datetime | None = None):
        self.now = now or datetime.utcnow()

    @staticmethod
    def _platform_norm(platform: str) -> float:
        return PLATFORM_NORM.get(platform, DEFAULT_NORM)

    def score_items(self, items: List[ChannelItem]) -> List[ChannelItem]:
        """Annotates each item with momentum metadata and returns them."""
        if not items:
            return items

        # Log-scaled normalization: log(1+raw)/log(1+ceiling) gives a smoother
        # curve than raw division (a 900-upvote post shouldn't beat a 850 one
        # by much, but both should crush a 12-upvote post).
        for it in items:
            raw = max(0, it.engagement_score or 0)
            ceiling = self._platform_norm(it.channel)
            norm = math.log1p(raw) / math.log1p(ceiling)
            norm = min(1.0, norm)

            credibility = PLATFORM_WEIGHTS.get(it.channel, 0.8)

            # Recency decay if the platform supplies a parseable timestamp
            age_days = None
            meta = it.raw_metadata or {}
            ts = meta.get("created_utc") or meta.get("published") or meta.get("timestamp")
            if ts:
                try:
                    if isinstance(ts, (int, float)):
                        age_days = max(0.0, (self.now.timestamp() - float(ts)) / 86400.0)
                    else:
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
                        age_days = max(0.0, (self.now - dt).total_seconds() / 86400.0)
                    age_days = min(age_days, 365.0)
                except Exception:
                    age_days = None

            if age_days is not None:
                # 7-day half-life
                recency = 0.5 ** (age_days / 7.0)
                recency = 0.35 + 0.65 * recency  # floor so old evidence isn't erased
            else:
                recency = 0.7  # neutral default when unknown

            momentum = round(100 * norm * credibility * recency, 1)
            meta = it.raw_metadata or {}
            meta["momentum_score"] = momentum
            meta["momentum_label"] = momentum_label(momentum)
            meta["engagement_normalized"] = round(norm, 3)
            meta["recency_factor"] = round(recency, 3)
            it.raw_metadata = meta

        return items

    @staticmethod
    def rank_key(item: ChannelItem) -> Tuple[float, int]:
        """Sort key: momentum desc, then raw engagement desc."""
        meta = item.raw_metadata or {}
        return (-meta.get("momentum_score", 0.0), -(item.engagement_score or 0))


class CrossSourceMerger:
    """Merges lookalike signals across platforms into single multi-source stories."""

    def __init__(
        self,
        similarity_threshold: float = 0.42,
        min_token_overlap: int = 4,
    ):
        self.similarity_threshold = similarity_threshold
        self.min_token_overlap = min_token_overlap

    # ------------------------------------------------------------------
    @staticmethod
    def _tokens(text: str) -> set:
        stop = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
            "to", "of", "in", "on", "for", "with", "at", "by", "from", "that",
            "this", "it", "as", "be", "has", "have", "had", "will", "would",
            "can", "could", "should", "not", "no", "yes", "do", "does", "did",
        }
        return set(re.findall(r"[a-z0-9]{3,}", text.lower())) - stop

    def _jaccard(self, a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    # ------------------------------------------------------------------
    def merge(self, items: List[ChannelItem]) -> Tuple[List[ChannelItem], List[Dict[str, Any]]]:
        """Greedy single-pass merging.

        Returns (merged_items, merge_records) where merge_records describe
        each merge for transparency ("same story found on Reddit and HN = one
        cluster, not two").
        """
        merged: List[ChannelItem] = []
        records: List[Dict[str, Any]] = []

        # Process highest-momentum first so primary stories keep their identity
        for item in items:
            target = None
            target_sim = 0.0
            for keeper in merged:
                sim = self._jaccard(self._tokens(item.title or ""), self._tokens(keeper.title or ""))
                # Titles are strong evidence; require either a high title match
                # or (medium title match + meaningful body overlap).
                if sim >= 0.60:
                    target = keeper
                    target_sim = sim
                    break
                if sim >= self.similarity_threshold:
                    body_sim = self._jaccard(
                        self._tokens(item.content or ""), self._tokens(keeper.content or "")
                    )
                    if body_sim >= 0.18:
                        target = keeper
                        target_sim = max(sim, body_sim)
                        break

            if target is not None:
                # Fold this item into the keeper as corroborating evidence
                meta = target.raw_metadata or {}
                sources = meta.setdefault("corroborating_sources", [])
                sources.append({
                    "channel": item.channel,
                    "url": item.url,
                    "title": item.title,
                    "engagement_score": item.engagement_score,
                    "momentum_score": (item.raw_metadata or {}).get("momentum_score"),
                })
                meta["cross_source_confirmed"] = True
                # Boost: cross-validated stories are more credible
                meta["momentum_score"] = round(
                    min(100.0, meta.get("momentum_score", 0.0) * 1.12 + 4.0), 1
                )
                meta["merge_similarity"] = round(target_sim, 3)
                target.raw_metadata = meta
                records.append({
                    "merged_external_id": item.external_id,
                    "into_external_id": target.external_id,
                    "from_channel": item.channel,
                    "into_channel": target.channel,
                    "similarity": round(target_sim, 3),
                })
            else:
                merged.append(item)

        return merged, records


def merge_cluster_duplicates(clusters: List[Dict[str, Any]], max_title_tokens: int = 200) -> List[Dict[str, Any]]:
    """Post-clustering pass: merge InsightCluster dicts whose titles/tokens overlap.

    The embedding clusterer can still split one story into two clusters
    (different wording, same theme). This pass merges clusters sharing
    dominant tokens, combining quotes and item counts, and preserving the
    highest-severity cluster's identity.
    """
    if len(clusters) <= 1:
        return clusters

    def norm_tokens(text: str) -> set:
        return set(CrossSourceMerger._tokens(text))

    kept: List[Dict[str, Any]] = []
    for cluster in sorted(
        clusters,
        key=lambda c: (-(c.get("severity_score") or 0), -(c.get("item_count") or 0)),
    ):
        target = None
        c_tokens = norm_tokens(cluster.get("title", ""))
        for keeper in kept:
            k_tokens = norm_tokens(keeper.get("title", ""))
            if not c_tokens or not k_tokens:
                continue
            sim = len(c_tokens & k_tokens) / len(c_tokens | k_tokens)
            # Merge when titles share most dominant tokens, or one is a subset
            # of the other (e.g. "API rate limits" & "Rate limits on the API")
            if sim >= 0.55 or (c_tokens <= k_tokens or k_tokens <= c_tokens):
                target = keeper
                break
        if target is not None:
            target["item_count"] = target.get("item_count", 0) + cluster.get("item_count", 0)
            existing_quotes = {q.get("permalink") for q in target.get("quotes", [])}
            for q in cluster.get("quotes", []):
                if q.get("permalink") not in existing_quotes:
                    target["quotes"].append(q)
            target["severity_score"] = round(
                max(target.get("severity_score", 0), cluster.get("severity_score", 0)), 2
            )
            platforms = set(target.get("keyword_tags", [])) | set(cluster.get("keyword_tags", []))
            target["keyword_tags"] = sorted(platforms)
            target.setdefault("merged_from", []).append(cluster.get("title"))
        else:
            kept.append(cluster)

    return kept
