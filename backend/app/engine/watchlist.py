"""Watchlist Engine — Trend Monitoring with Delta Diffs (last30days pattern)

Persists a compact metrics snapshot for every watchlist research run, then
diffs consecutive snapshots to surface "what changed since the last sweep":
new pain clusters, resolved themes, severity shifts, volume moves.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def build_snapshot(clusters: List[Dict[str, Any]], total_items: int, query: str) -> Dict[str, Any]:
    """Builds a compact, diffable snapshot from a completed research run."""
    theme_entries = []
    for c in clusters:
        theme_entries.append({
            "title": (c.get("title") or "")[:200],
            "category": c.get("category"),
            "severity": c.get("severity_score", 0),
            "item_count": c.get("item_count", 0),
            "top_quote": (c.get("quotes") or [{}])[0].get("quote_text", "")[:180],
            "permalink": (c.get("quotes") or [{}])[0].get("permalink", ""),
        })
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "total_items": total_items,
        "clusters_count": len(clusters),
        "themes": theme_entries[:12],
    }


def diff_snapshots(
    current: Dict[str, Any],
    previous: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Diffs the current snapshot against the previous run's snapshot.

    Theme identity is matched with token-overlap so 'API rate limits overnight'
    and 'Rate limits on API requests' count as the same theme.
    """
    if not previous:
        return {
            "has_previous": False,
            "status": "BASELINE",
            "new_themes": [t["title"] for t in current.get("themes", [])[:5]],
            "resolved_themes": [],
            "worsening_themes": [],
            "improving_themes": [],
            "volume_delta": 0,
            "note": "First watchlist run — baseline established.",
        }

    def toks(text: str) -> set:
        stop = {"the", "a", "an", "and", "or", "for", "with", "on", "in", "of", "to"}
        return {w for w in text.lower().split() if w not in stop} or {text.lower()}

    prev_themes = previous.get("themes", [])
    curr_themes = current.get("themes", [])

    def find_match(theme: Dict[str, Any], pool: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        t_tokens = toks(theme.get("title", ""))
        best, best_sim = None, 0.0
        for cand in pool:
            c_tokens = toks(cand.get("title", ""))
            if not t_tokens or not c_tokens:
                continue
            sim = len(t_tokens & c_tokens) / len(t_tokens | c_tokens)
            if sim > best_sim:
                best, best_sim = cand, sim
        return best if best_sim >= 0.4 else None

    new_themes, worsening, improving = [], [], []
    matched_prev = []

    for t in curr_themes:
        match = find_match(t, prev_themes)
        if match is None:
            new_themes.append(t)
        else:
            matched_prev.append(match)
            sev_delta = (t.get("severity") or 0) - (match.get("severity") or 0)
            vol_delta = (t.get("item_count") or 0) - (match.get("item_count") or 0)
            entry = {
                "title": t["title"],
                "severity_delta": round(sev_delta, 2),
                "volume_delta": vol_delta,
            }
            if sev_delta >= 0.08 or vol_delta >= 3:
                worsening.append(entry)
            elif sev_delta <= -0.08 or vol_delta <= -3:
                improving.append(entry)

    resolved = []
    for p in prev_themes:
        if find_match(p, curr_themes) is None:
            resolved.append(p.get("title", ""))

    volume_delta = (current.get("total_items") or 0) - (previous.get("total_items") or 0)

    if new_themes and (worsening or volume_delta > 0):
        status = "HEATING_UP"
    elif worsening:
        status = "WORSENING"
    elif new_themes:
        status = "EMERGING"
    elif improving:
        status = "COOLING"
    else:
        status = "STABLE"

    return {
        "has_previous": True,
        "status": status,
        "previous_timestamp": previous.get("timestamp"),
        "new_themes": [t["title"] for t in new_themes[:8]],
        "resolved_themes": resolved[:8],
        "worsening_themes": worsening[:8],
        "improving_themes": improving[:8],
        "volume_delta": volume_delta,
    }
