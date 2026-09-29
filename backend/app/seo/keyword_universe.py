"""Keyword Universe Builder — Intent Classification & Topic Clustering
(notfair `keyword-research` pattern, applied to on-page + seed expansion)

Extends the single-page keyword analyzer into a full universe: seed terms
from page content expanded with modifier templates, classified by search
intent (informational / commercial / transactional / navigational), and
grouped into topic clusters for content planning.
"""
import re
from collections import Counter
from typing import Dict, Any, List

from app.seo.keyword_gap import STOP_WORDS

# Modifier templates for seed expansion (search-demand patterns)
MODIFIER_TEMPLATES = {
    "Informational": ["how to {k}", "what is {k}", "{k} guide", "{k} tutorial", "{k} explained", "why {k}"],
    "Commercial": ["best {k}", "{k} alternatives", "{k} vs", "top {k}", "{k} review", "{k} comparison"],
    "Transactional": ["{k} pricing", "buy {k}", "{k} download", "{k} api", "{k} pricing plans", "get {k}"],
    "Navigational / Brand": ["{k} login", "{k} docs", "{k} dashboard", "{k} support"],
}

# Head-term extraction: prefer bigrams/trigrams around top unigrams
def _top_unigrams(text: str, limit: int = 10) -> List[str]:
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text) if w.lower() not in STOP_WORDS]
    return [w for w, _ in Counter(words).most_common(limit)]


def _top_bigrams(text: str, limit: int = 8) -> List[str]:
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)]
    bigrams = [
        f"{words[i]} {words[i+1]}"
        for i in range(len(words) - 1)
        if words[i] not in STOP_WORDS and words[i + 1] not in STOP_WORDS
    ]
    return [b for b, _ in Counter(bigrams).most_common(limit)]


def classify_intent(keyword: str) -> str:
    k = keyword.lower()
    if any(t in k for t in ["how ", "what ", "why ", "guide", "tutorial", "explained", "learn"]):
        return "Informational"
    if any(t in k for t in ["best", "vs", "alternative", "review", "comparison", "top "]):
        return "Commercial"
    if any(t in k for t in ["pricing", "buy", "download", "get ", "coupon", "discount", "hire"]):
        return "Transactional"
    return "Navigational / Brand"


class KeywordUniverseBuilder:
    def build(self, visible_text: str, headings: Dict[str, Any], meta_description: str = "") -> Dict[str, Any]:
        seed_pool = " ".join([
            " ".join(headings.get("h1", []) or []),
            " ".join(headings.get("h2", []) or []),
            meta_description or "",
            visible_text or "",
        ])

        unigrams = _top_unigrams(seed_pool, 10)
        bigrams = _top_bigrams(seed_pool, 8)

        # Head terms = strongest bigrams, falling back to top unigrams
        head_terms = bigrams[:5] or unigrams[:5]

        universe: List[Dict[str, Any]] = []
        seen = set()
        for head in head_terms:
            for intent, templates in MODIFIER_TEMPLATES.items():
                for tpl in templates:
                    kw = tpl.format(k=head)
                    if kw in seen:
                        continue
                    seen.add(kw)
                    universe.append({
                        "keyword": kw,
                        "head_term": head,
                        "intent": intent,
                        # Estimated difficulty: head-term competition heuristic
                        "difficulty_estimate": min(90, 25 + 6 * head.count(" ") * 5 + len(head) // 3),
                        "priority": "HIGH" if intent in ("Commercial", "Transactional") else "MEDIUM",
                    })

        # Topic clusters: group expansions by head term
        clusters = []
        for head in head_terms:
            members = [u for u in universe if u["head_term"] == head]
            if not members:
                continue
            intent_mix = Counter(m["intent"] for m in members)
            clusters.append({
                "cluster_topic": head,
                "keyword_count": len(members),
                "dominant_intent": intent_mix.most_common(1)[0][0],
                "pillars": [m["keyword"] for m in members if m["intent"] == "Informational"][:4],
                "money_pages": [m["keyword"] for m in members if m["intent"] in ("Commercial", "Transactional")][:4],
            })

        return {
            "seed_terms": {"unigrams": unigrams, "bigrams": bigrams},
            "universe_size": len(universe),
            "universe": universe[:60],
            "topic_clusters": clusters,
            "content_gap_flags": [
                "No pricing/comparison coverage detected" if not any(u["intent"] == "Commercial" for u in universe) else None,
                "No how-to/educational coverage detected" if not any(u["intent"] == "Informational" for u in universe) else None,
            ],
        }
