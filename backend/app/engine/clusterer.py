"""Semantic Theme Clustering & Multi-Platform Synthesis Engine"""
import logging
from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from app.channels.base import ChannelItem

logger = logging.getLogger(__name__)

PAIN_KEYWORDS = ["bug", "slow", "error", "latency", "broken", "issue", "crash", "timeout", "frustrat", "fail", "hard", "leak", "horrible", "terrible"]
WORKAROUND_KEYWORDS = ["hack", "workaround", "wrapper", "custom", "patch", "script", "bypass", "manual", "instead of", "had to", "forked"]
DESIRE_KEYWORDS = ["wish", "hope", "need", "feature request", "why can't", "should support", "missing", "please add", "would be great", "roadmap"]
CHURN_KEYWORDS = ["migrat", "switched to", "moved to", "left", "cancelled", "ditching", "alternative", "expensive", "pricing cliff", "rip off"]

class SemanticClusterer:
    def cluster_items(self, items: List[ChannelItem], embeddings: np.ndarray) -> List[Dict[str, Any]]:
        n_items = len(items)
        if n_items == 0:
            return []
        
        # Adaptive number of clusters based on sample size
        if n_items <= 5:
            n_clusters = max(1, n_items)
        elif n_items <= 25:
            n_clusters = 3
        elif n_items <= 60:
            n_clusters = 5
        elif n_items <= 120:
            n_clusters = 6
        else:
            n_clusters = 8

        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='cosine',
                linkage='average'
            )
            labels = clustering.fit_predict(embeddings)
        except Exception as e:
            logger.warning(f"Clustering error fallback: {e}")
            labels = np.zeros(n_items, dtype=int)

        clusters = []
        unique_labels = sorted(list(set(labels)))

        for label in unique_labels:
            cluster_indices = [i for i, l in enumerate(labels) if l == label]
            cluster_items = [items[i] for i in cluster_indices]
            
            # 1. Aggregate Laya System 1 category votes & calibrated severities
            category_counts = {}
            severity_vals = []
            for it in cluster_items:
                meta = it.raw_metadata or {}
                if "laya_category" in meta:
                    cat = meta["laya_category"]
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                if "laya_severity" in meta:
                    severity_vals.append(float(meta["laya_severity"]))

            if category_counts:
                best_cat = max(category_counts, key=category_counts.get)
            else:
                # Heuristic keyword fallback
                combined_text = " ".join([it.content.lower() for it in cluster_items])
                cat_scores = {
                    "PAIN_POINT": sum(combined_text.count(k) for k in PAIN_KEYWORDS),
                    "WORKAROUND": sum(combined_text.count(k) for k in WORKAROUND_KEYWORDS),
                    "DESIRE": sum(combined_text.count(k) for k in DESIRE_KEYWORDS),
                    "CHURN_TRIGGER": sum(combined_text.count(k) for k in CHURN_KEYWORDS)
                }
                best_cat = max(cat_scores, key=cat_scores.get)
                if cat_scores[best_cat] == 0:
                    categories = ["PAIN_POINT", "DESIRE", "WORKAROUND", "CHURN_TRIGGER"]
                    best_cat = categories[label % len(categories)]

            # Derive title from most engaged item or top words
            top_item = max(cluster_items, key=lambda x: x.engagement_score)
            title = top_item.title if top_item.title else f"Discussion on {top_item.channel.title()} Theme"
            if len(title) > 95:
                title = title[:92] + "..."

            # Real calibrated severity calculation
            if severity_vals:
                base_sev = float(np.mean(severity_vals))
                severity = round(min(0.98, max(0.40, base_sev + (len(cluster_items) / (n_items + 1)) * 0.15)), 2)
            else:
                base_severity = 0.75 if best_cat in ["PAIN_POINT", "CHURN_TRIGGER"] else 0.55
                severity = round(min(0.98, base_severity + (len(cluster_items) / (n_items + 1)) * 0.35), 2)

            # Sourced platforms
            platforms_present = sorted(list(set(it.channel for it in cluster_items)))

            # Extract top 6 verbatim quotes sorted by engagement
            sorted_by_engagement = sorted(cluster_items, key=lambda x: x.engagement_score, reverse=True)
            quotes = []
            for item in sorted_by_engagement[:6]:
                excerpt = item.content.strip()
                if len(excerpt) > 300:
                    excerpt = excerpt[:297] + "..."
                quotes.append({
                    "quote_text": excerpt,
                    "permalink": item.url,
                    "source_author": item.author,
                    "source_channel": item.channel,
                    "engagement_score": item.engagement_score
                })

            clusters.append({
                "title": title,
                "category": best_cat,
                "description": f"Encountered across {len(cluster_items)} signals from {', '.join(platforms_present)}. Community discussions highlight recurring friction and explicit demand for improvements.",
                "severity_score": round(severity, 2),
                "item_count": len(cluster_items),
                "keyword_tags": [best_cat.lower().replace("_", "-"), f"{len(cluster_items)}-signals"] + platforms_present,
                "quotes": quotes
            })

        return clusters
