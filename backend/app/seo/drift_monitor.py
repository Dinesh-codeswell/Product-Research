"""SEO Drift & Baseline Regression Monitor
Compares current page SEO state against baseline snapshot to detect regressions.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

class DriftMonitor:
    def create_snapshot(self, crawl_data: Dict[str, Any], overall_score: int) -> Dict[str, Any]:
        """Creates a serialized baseline snapshot for a URL."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": crawl_data.get("status_code", 200),
            "overall_score": overall_score,
            "title": crawl_data.get("title", {}).get("text", ""),
            "title_length": crawl_data.get("title", {}).get("length", 0),
            "meta_description": crawl_data.get("meta_description", {}).get("text", ""),
            "meta_desc_length": crawl_data.get("meta_description", {}).get("length", 0),
            "h1_count": crawl_data.get("headings", {}).get("h1_count", 0),
            "h1_sample": crawl_data.get("headings", {}).get("h1", [""])[0] if crawl_data.get("headings", {}).get("h1") else "",
            "schema_count": len(crawl_data.get("json_ld_schemas", [])),
            "canonical_url": crawl_data.get("canonical", {}).get("url", ""),
            "has_og_title": bool(crawl_data.get("open_graph", {}).get("title")),
            "has_og_image": bool(crawl_data.get("open_graph", {}).get("image")),
            "has_twitter_card": bool(crawl_data.get("twitter_card", {}).get("card")),
            "word_count": crawl_data.get("word_count", 0)
        }

    def compare(self, current_data: Dict[str, Any], current_score: int, baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compares current live audit metrics against baseline snapshot."""
        if not baseline:
            return {
                "has_baseline": False,
                "drift_status": "NO_BASELINE",
                "score_delta": 0,
                "regressions": [],
                "improvements": [],
                "note": "No prior baseline snapshot found. Current audit established as baseline."
            }

        regressions = []
        improvements = []

        curr_title = current_data.get("title", {}).get("text", "")
        base_title = baseline.get("title", "")
        if base_title and not curr_title:
            regressions.append("CRITICAL: Title tag was removed or is now empty.")
        elif curr_title != base_title:
            improvements.append(f"Title changed from '{base_title[:40]}...' to '{curr_title[:40]}...'")

        curr_desc = current_data.get("meta_description", {}).get("text", "")
        base_desc = baseline.get("meta_description", "")
        if base_desc and not curr_desc:
            regressions.append("HIGH: Meta description was removed.")
        elif not base_desc and curr_desc:
            improvements.append("HIGH: Added missing meta description.")

        curr_h1 = current_data.get("headings", {}).get("h1_count", 0)
        base_h1 = baseline.get("h1_count", 0)
        if base_h1 == 1 and curr_h1 == 0:
            regressions.append("HIGH: Primary <h1> heading was removed.")
        elif base_h1 == 0 and curr_h1 == 1:
            improvements.append("HIGH: Added primary <h1> heading.")

        curr_schemas = len(current_data.get("json_ld_schemas", []))
        base_schemas = baseline.get("schema_count", 0)
        if curr_schemas < base_schemas:
            regressions.append(f"MEDIUM: JSON-LD schemas dropped from {base_schemas} to {curr_schemas}.")
        elif curr_schemas > base_schemas:
            improvements.append(f"MEDIUM: Added {curr_schemas - base_schemas} new JSON-LD schemas.")

        curr_words = current_data.get("word_count", 0)
        base_words = baseline.get("word_count", 0)
        if base_words > 0 and curr_words < base_words * 0.7:
            regressions.append(f"HIGH: Substantial content loss detected ({curr_words} words vs baseline {base_words}).")
        elif base_words > 0 and curr_words > base_words * 1.3:
            improvements.append(f"Content volume expanded ({curr_words} words vs baseline {base_words}).")

        score_delta = current_score - baseline.get("overall_score", current_score)

        if regressions:
            drift_status = "REGRESSION_DETECTED"
        elif improvements:
            drift_status = "IMPROVEMENTS_DETECTED"
        else:
            drift_status = "STABLE"

        return {
            "has_baseline": True,
            "baseline_timestamp": baseline.get("timestamp"),
            "drift_status": drift_status,
            "score_delta": score_delta,
            "regressions": regressions,
            "improvements": improvements,
            "baseline_metrics": baseline
        }
