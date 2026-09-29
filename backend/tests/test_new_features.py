"""Tests for P0 research pipeline upgrades: momentum scoring, cross-source
merging, cluster dedup, discovery, watchlist snapshots/diffs, automations,
and the new channels."""
import asyncio

import pytest

from app.channels.base import ChannelItem
from app.engine.signals import MomentumScorer, CrossSourceMerger, merge_cluster_duplicates
from app.engine.watchlist import build_snapshot, diff_snapshots


def _item(title: str, content: str, channel: str, engagement: int = 100) -> ChannelItem:
    return ChannelItem(
        external_id=f"{channel}_{hash(title)}",
        channel=channel,
        url=f"https://example.com/{hash(title)}",
        title=title,
        content=content,
        author="tester",
        engagement_score=engagement,
        raw_metadata={},
    )


# ============================================================================
# Momentum scoring
# ============================================================================

def test_momentum_scales_with_engagement():
    scorer = MomentumScorer()
    items = [
        _item("Low", "content low", "reddit", engagement=10),
        _item("Mid", "content mid", "reddit", engagement=200),
        _item("High", "content high", "reddit", engagement=5000),
    ]
    scorer.score_items(items)
    scores = [it.raw_metadata["momentum_score"] for it in items]
    assert scores[0] < scores[1] < scores[2]
    assert all(0 <= s <= 100 for s in scores)
    assert all("momentum_label" in it.raw_metadata for it in items)


def test_momentum_labels():
    assert MomentumScorer and callable(MomentumScorer)
    from app.engine.signals import momentum_label
    assert momentum_label(90) == "SURGING"
    assert momentum_label(60) == "RISING"
    assert momentum_label(40) == "STEADY"
    assert momentum_label(10) == "FADING"


def test_momentum_handles_garbage_timestamps():
    scorer = MomentumScorer()
    it = _item("t", "c", "reddit")
    it.raw_metadata = {"created_utc": "not-a-date"}
    scorer.score_items([it])
    assert "momentum_score" in it.raw_metadata


# ============================================================================
# Cross-source merging
# ============================================================================

def test_cross_source_merger_combines_same_story():
    scorer = MomentumScorer()
    items = [
        _item("Supabase vs Firebase debate", "supabase firebase debate content", "reddit", 500),
        _item("Supabase vs Firebase debate", "supabase firebase debate on hn", "hackernews", 300),
        _item("Unrelated topic about databases", "totally different subject matter", "youtube", 100),
    ]
    scorer.score_items(items)
    merged, records = CrossSourceMerger().merge(items)
    assert len(merged) == 2
    assert len(records) == 1
    story = [m for m in merged if (m.raw_metadata or {}).get("cross_source_confirmed")]
    assert len(story) == 1
    assert story[0].raw_metadata["corroborating_sources"][0]["channel"] == "hackernews"


def test_cross_source_merger_keeps_distinct_stories():
    items = [
        _item("Pricing complaints about tool X", "tool x pricing too expensive", "reddit", 100),
        _item("New AI model released today", "brand new model launch", "hackernews", 100),
    ]
    merged, records = CrossSourceMerger().merge(items)
    assert len(merged) == 2
    assert records == []


# ============================================================================
# Cluster dedup
# ============================================================================

def test_merge_cluster_duplicates():
    clusters = [
        {
            "title": "API rate limits frustration",
            "category": "PAIN_POINT",
            "severity_score": 0.8,
            "item_count": 5,
            "keyword_tags": ["reddit"],
            "quotes": [{"quote_text": "q1", "permalink": "https://a"}],
        },
        {
            "title": "Rate limits on the API",
            "category": "PAIN_POINT",
            "severity_score": 0.6,
            "item_count": 3,
            "keyword_tags": ["youtube"],
            "quotes": [{"quote_text": "q2", "permalink": "https://b"}],
        },
        {
            "title": "Pricing is too expensive",
            "category": "CHURN_TRIGGER",
            "severity_score": 0.7,
            "item_count": 4,
            "keyword_tags": ["reddit"],
            "quotes": [],
        },
    ]
    merged = merge_cluster_duplicates(clusters)
    assert len(merged) == 2
    rate_cluster = next(c for c in merged if "rate limits" in c["title"].lower())
    assert rate_cluster["item_count"] == 8
    assert {q["permalink"] for q in rate_cluster["quotes"]} == {"https://a", "https://b"}


# ============================================================================
# Watchlist snapshots & diffs
# ============================================================================

def test_watchlist_baseline_and_delta():
    prev_clusters = [
        {"title": "Slow build times", "category": "PAIN_POINT", "severity_score": 0.6,
         "item_count": 10, "quotes": []},
        {"title": "Missing dark mode", "category": "DESIRE", "severity_score": 0.4,
         "item_count": 5, "quotes": []},
    ]
    prev = build_snapshot(prev_clusters, 40, "test topic")

    curr_clusters = [
        {"title": "Slow build times worse", "category": "PAIN_POINT", "severity_score": 0.85,
         "item_count": 18, "quotes": []},
        {"title": "Missing dark mode", "category": "DESIRE", "severity_score": 0.4,
         "item_count": 5, "quotes": []},
        {"title": "Broken CLI on Windows", "category": "PAIN_POINT", "severity_score": 0.75,
         "item_count": 7, "quotes": []},
    ]
    curr = build_snapshot(curr_clusters, 52, "test topic")

    baseline_diff = diff_snapshots(curr, None)
    assert baseline_diff["status"] == "BASELINE"

    delta = diff_snapshots(curr, prev)
    assert delta["has_previous"]
    assert delta["status"] in ("HEATING_UP", "WORSENING")
    assert any("CLI" in t for t in delta["new_themes"])
    assert any("build times" in t["title"].lower() for t in delta["worsening_themes"])
    assert delta["volume_delta"] == 12


# ============================================================================
# Automation rules
# ============================================================================

def test_automation_rule_matching():
    from app.engine.automations import _rule_matches
    from app.models.workflow_entities import AutomationRule

    rule = AutomationRule(
        id="r1", name="test", event_type="research.completed",
        conditions={"min_severity": 0.8}, action_type="webhook", action_config={},
    )
    payload_hot = {"query": "ai tools", "clusters_count": 3, "clusters": [{"severity_score": 0.9}]}
    payload_cold = {"query": "ai tools", "clusters_count": 3, "clusters": [{"severity_score": 0.5}]}

    assert _rule_matches(rule, "research.completed", payload_hot)
    assert not _rule_matches(rule, "research.completed", payload_cold)
    assert not _rule_matches(rule, "seo.completed", payload_hot)


def test_automation_seo_score_condition():
    from app.engine.automations import _rule_matches
    from app.models.workflow_entities import AutomationRule

    rule = AutomationRule(
        id="r2", name="test", event_type="seo.completed",
        conditions={"score_below": 60}, action_type="webhook", action_config={},
    )
    assert _rule_matches(rule, "seo.completed", {"overall_score": 45, "domain": "x.com"})
    assert not _rule_matches(rule, "seo.completed", {"overall_score": 85, "domain": "x.com"})


# ============================================================================
# Diagram agent
# ============================================================================

def test_diagram_agent_generates_valid_svg():
    from app.engine.diagram_agent import DiagramAgent

    md = """# PRD
## Problem Statement
Stuff is broken.
## Functional Requirements
- **FR-1 (Auto Detection):** System shall detect failures.
- **FR-2 (Cost Profiling):** Provide real-time estimates.
## Success Metrics
Reduce churn by 35%.
"""
    agent = DiagramAgent()
    result = agent.generate(md, title="Test")
    assert result["success"]
    assert result["svg"].startswith("<svg")
    assert 'viewBox="0 0 960 540"' in result["svg"]
    assert result["node_count"] >= 2
    # Critic pass must not leave overlapping nodes
    assert not result["critique"].get("remaining")


def test_diagram_agent_handles_empty_doc():
    from app.engine.diagram_agent import DiagramAgent

    result = DiagramAgent().generate("", title="Empty")
    assert result["success"]
    assert result["node_count"] >= 2


# ============================================================================
# Keyword universe & content planner
# ============================================================================

def test_keyword_universe_builder():
    from app.seo.keyword_universe import KeywordUniverseBuilder

    builder = KeywordUniverseBuilder()
    result = builder.build(
        visible_text="Generative Engine Optimization helps AI citations. Generative Engine Optimization uses evidence density.",
        headings={"h1": ["Generative Engine Optimization"], "h2": ["What is Generative Engine Optimization?"]},
        meta_description="Learn generative engine optimization",
    )
    assert result["universe_size"] > 0
    assert len(result["topic_clusters"]) > 0
    cluster = result["topic_clusters"][0]
    assert "dominant_intent" in cluster
    assert all(k["intent"] in ("Informational", "Commercial", "Transactional", "Navigational / Brand") for k in result["universe"])


def test_content_planner_builds_calendar():
    from app.seo.content_planner import ContentPlanner
    from app.seo.keyword_universe import KeywordUniverseBuilder

    universe = KeywordUniverseBuilder().build(
        visible_text="Deploy servers with docker. Docker deploy pipelines.",
        headings={"h1": ["Docker Deploy"], "h2": ["How to deploy with docker"]},
    )
    plan = ContentPlanner().build_plan(universe, posts_per_week=2, horizon_weeks=2)
    assert plan["success"]
    assert len(plan["calendar"]) <= 4
    assert all("publish_date" in t for t in plan["calendar"])
    assert plan["summary"]["total_planned"] == len(plan["calendar"])


# ============================================================================
# Brief renderer
# ============================================================================

def test_research_brief_renders():
    from app.engine.brief_renderer import render_brief_html

    html = render_brief_html("research", {
        "query": "test", "channels": ["reddit"], "total_items": 10,
        "summary": "Summary text",
        "clusters": [{"title": "C1", "category": "PAIN_POINT", "description": "d",
                      "severity_score": 0.9, "item_count": 4, "quotes": []}],
        "feedbacks": [{"channel": "reddit", "url": "https://x", "title": "T", "engagement": 5}],
    })
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "C1" in html


def test_seo_brief_renders():
    from app.engine.brief_renderer import render_brief_html

    html = render_brief_html("seo", {
        "url": "https://example.com", "domain": "example.com", "audit_type": "quick",
        "overall_score": 72, "technical_score": 80, "geo_readiness_score": 60,
        "onpage_score": 70, "image_score": 90,
        "executive_summary": "- issue one\n- issue two",
        "results": {"geo": {"pillars": {}}, "technical": {"issues": []}},
    })
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "example.com" in html
