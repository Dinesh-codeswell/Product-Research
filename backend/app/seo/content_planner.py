"""Content Planner — Editorial Calendar from Keyword Opportunities
(notfair `content-planner` pattern)

Turns the keyword universe + existing content inventory into a prioritized,
dated editorial calendar: pillar pages first, then supporting cluster
articles, then conversion pages. Output is exportable via the Office studio.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _cadence_start(weeks_ahead: int = 0) -> datetime:
    """Next Monday at 00:00 as the calendar anchor."""
    today = datetime.utcnow().date()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    monday = today + timedelta(days=days_until_monday + weeks_ahead * 7)
    return datetime(monday.year, monday.month, monday.day)


class ContentPlanner:
    def build_plan(
        self,
        keyword_universe: Dict[str, Any],
        existing_content_hints: Optional[List[str]] = None,
        posts_per_week: int = 2,
        horizon_weeks: int = 6,
        domain: str = "",
    ) -> Dict[str, Any]:
        """Builds a dated editorial calendar from keyword universe clusters.

        existing_content_hints: list of existing page titles/URLs on the site,
        used to avoid duplicating coverage and to flag refresh candidates.
        """
        clusters = keyword_universe.get("topic_clusters", []) or []
        existing = [h.lower() for h in (existing_content_hints or [])]

        # Build the prioritized task list: pillars first, then money pages,
        # then supporting informational articles.
        tasks: List[Dict[str, Any]] = []

        for cluster in clusters:
            head = cluster.get("cluster_topic", "")
            title_case = head.title()
            refresh = any(head in ex for ex in existing)

            tasks.append({
                "type": "PILLAR_PAGE",
                "title": f"{title_case}: The Complete Guide",
                "target_keyword": head,
                "cluster": head,
                "priority": 1 if not refresh else 3,
                "refresh_candidate": refresh,
                "target_url": f"/{_slug(head)}",
                "effort": "high",
                "outline": [
                    f"What is {title_case}?",
                    f"How {title_case} works (with diagram)",
                    f"{title_case} comparison table",
                    "Common pitfalls & fixes",
                    "FAQ (schema-ready)",
                ],
            })

            for kw in (cluster.get("money_pages") or [])[:2]:
                kw_title = kw.title()
                tasks.append({
                    "type": "CONVERSION_PAGE",
                    "title": kw_title,
                    "target_keyword": kw,
                    "cluster": head,
                    "priority": 2,
                    "refresh_candidate": any(kw in ex for ex in existing),
                    "target_url": f"/{_slug(kw)}",
                    "effort": "medium",
                    "outline": ["Problem framing", "Solution overview", "Pricing/comparison table", "CTA"],
                })

            for kw in (cluster.get("pillars") or [])[:2]:
                kw_title = kw.title()
                tasks.append({
                    "type": "SUPPORTING_ARTICLE",
                    "title": kw_title,
                    "target_keyword": kw,
                    "cluster": head,
                    "priority": 3,
                    "refresh_candidate": any(kw in ex for ex in existing),
                    "target_url": f"/{_slug(kw)}",
                    "effort": "low",
                    "outline": ["Direct answer (paragraph 1)", "Step-by-step", "Evidence & stats", "Internal links to pillar"],
                })

        # Sort by priority then effort; assign dates by cadence
        tasks.sort(key=lambda t: (t["priority"], 0 if t["effort"] == "high" else 1))
        tasks = tasks[: horizon_weeks * posts_per_week]

        anchor = _cadence_start()
        for idx, task in enumerate(tasks):
            week = idx // posts_per_week
            slot = idx % posts_per_week
            publish_date = anchor + timedelta(days=week * 7 + slot * 3)  # Mon / Thu slots
            task["publish_date"] = publish_date.strftime("%Y-%m-%d")
            task["week"] = f"Week {week + 1}"

        total_refresh = sum(1 for t in tasks if t.get("refresh_candidate"))
        intent_coverage: Dict[str, int] = {}
        for t in tasks:
            kw = t.get("target_keyword", "")
            if any(x in kw for x in ("pricing", "buy", "download")):
                intent_coverage["Transactional"] = intent_coverage.get("Transactional", 0) + 1
            elif any(x in kw for x in ("best", "vs", "alternative", "review")):
                intent_coverage["Commercial"] = intent_coverage.get("Commercial", 0) + 1
            elif any(x in kw for x in ("how", "what", "why", "guide")):
                intent_coverage["Informational"] = intent_coverage.get("Informational", 0) + 1
            else:
                intent_coverage["Brand / Other"] = intent_coverage.get("Brand / Other", 0) + 1

        return {
            "success": True,
            "domain": domain,
            "cadence": f"{posts_per_week} posts/week",
            "horizon_weeks": horizon_weeks,
            "calendar": tasks,
            "summary": {
                "total_planned": len(tasks),
                "pillar_pages": sum(1 for t in tasks if t["type"] == "PILLAR_PAGE"),
                "conversion_pages": sum(1 for t in tasks if t["type"] == "CONVERSION_PAGE"),
                "supporting_articles": sum(1 for t in tasks if t["type"] == "SUPPORTING_ARTICLE"),
                "refresh_candidates": total_refresh,
                "intent_coverage": intent_coverage,
            },
            "recommendations": [
                "Publish pillar pages before their supporting articles so internal links have a destination.",
                "Add FAQPage JSON-LD to every supporting article (the schema generator already outputs it).",
                f"{total_refresh} planned items overlap existing content — schedule them as refreshes (higher ROI than net-new).",
            ] if total_refresh else [
                "Publish pillar pages before their supporting articles so internal links have a destination.",
                "Add FAQPage JSON-LD to every supporting article (the schema generator already outputs it).",
            ],
        }
