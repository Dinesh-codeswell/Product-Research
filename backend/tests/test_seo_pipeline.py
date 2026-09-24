"""Unit Tests for SEO & Generative Engine Optimization (GEO) Pipeline"""
import pytest
from app.seo.crawler import TechnicalCrawler
from app.seo.geo_optimizer import GeoOptimizer
from app.seo.schema_generator import SchemaGenerator
from app.seo.meta_generator import MetaGenerator
from app.seo.image_auditor import ImageSeoAuditor
from app.seo.keyword_gap import KeywordAndContentAnalyzer
from app.seo.drift_monitor import DriftMonitor
from app.seo.engine import SeoAuditEngine

MOCK_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>PulseRadar — Autonomous Consumer & SEO Intelligence Platform</title>
    <meta name="description" content="Discover verified customer friction, market sentiment, and 4-pillar Generative Engine Optimization (GEO) for AI search citations with PulseRadar.">
    <link rel="canonical" href="https://pulseradar.dev/">
    <meta property="og:title" content="PulseRadar — Autonomous Intelligence">
    <meta property="og:description" content="AI search citation and customer discovery.">
    <meta property="og:image" content="https://pulseradar.dev/og.png">
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Organization", "name": "PulseRadar", "url": "https://pulseradar.dev"}
    </script>
</head>
<body>
    <h1>Autonomous Product Discovery & SEO Intelligence</h1>
    <h2>What is Generative Engine Optimization?</h2>
    <p>Generative Engine Optimization (GEO) is the practice of structuring digital content so LLMs like ChatGPT, Perplexity, and Gemini can cite it accurately. According to research, 85% of AI answers rely on structured evidence density.</p>
    <h2>How does PulseRadar optimize for AI citations?</h2>
    <p>PulseRadar evaluates 4 core pillars: evidence density (35%), structure and position (25%), authority signals (25%), and machine crawlability (15%). Over 160 signals are verified in real time.</p>
    <ul>
        <li>Over 15,000 queries processed daily with 99.4% precision</li>
        <li>Direct integration with Firecrawl SDK and Playwright headless engine</li>
        <li>Automatic JSON-LD schema generation for organizations and web applications</li>
    </ul>
    <img src="/logo.webp" alt="PulseRadar Architecture Logo" width="200" height="60" loading="lazy">
    <a href="https://pulseradar.dev/docs">Documentation</a>
    <a href="https://github.com/pulseradar">GitHub Repository</a>
    <a href="https://twitter.com/pulseradar">Twitter / X</a>
</body>
</html>
"""

def test_geo_optimizer():
    geo = GeoOptimizer()
    crawl_data = {
        "raw_html": MOCK_HTML,
        "visible_text": "Autonomous Product Discovery & SEO Intelligence. What is Generative Engine Optimization? Over 15,000 queries processed daily with 99.4% precision. PulseRadar evaluates 4 core pillars.",
        "word_count": 350,
        "headings": {"h1_count": 1, "h2_count": 2, "h1": ["Autonomous Product Discovery"], "h2": ["What is Generative Engine Optimization?", "How does PulseRadar optimize?"]},
        "json_ld_schemas": [{"@context": "https://schema.org", "@type": "Organization", "name": "PulseRadar"}],
        "links": {"external_count": 2, "external_sample": ["https://github.com/pulseradar", "https://twitter.com/pulseradar"]},
        "title": {"text": "PulseRadar — Autonomous Consumer & SEO Intelligence Platform"},
        "meta_description": {"text": "Discover verified customer friction and 4-pillar Generative Engine Optimization."},
        "open_graph": {"title": "PulseRadar", "description": "AI search citation"},
        "robots": {"noindex": False}
    }
    res = geo.evaluate(crawl_data)
    assert res["overall_score"] > 50
    assert "evidence_density" in res["pillars"]
    assert "structure_and_position" in res["pillars"]
    assert "authority_signals" in res["pillars"]
    assert "ai_crawlability" in res["pillars"]
    assert len(res["recommendations"]) >= 0

def test_schema_generator():
    generator = SchemaGenerator()
    crawl_data = {
        "title": {"text": "PulseRadar Documentation"},
        "meta_description": {"text": "Explore architecture and API docs"},
        "headings": {"h1": ["Developer Guide"], "h2": ["What is PulseRadar?", "How to deploy?"]},
        "open_graph": {"image": "https://pulseradar.dev/og.png"},
        "links": {"external_sample": ["https://twitter.com/pulseradar", "https://github.com/pulseradar"]}
    }
    schemas = generator.generate_all("https://pulseradar.dev/docs/guide", crawl_data)
    assert "website" in schemas["generated_templates"]
    assert "organization" in schemas["generated_templates"]
    assert "breadcrumb" in schemas["generated_templates"]
    assert "faq" in schemas["generated_templates"]
    assert schemas["generated_templates"]["organization"]["name"] == "Pulseradar"

def test_meta_generator():
    gen = MetaGenerator()
    crawl_data = {
        "title": {"text": "PulseRadar Studio"},
        "meta_description": {"text": "Verified research and intelligence"},
        "headings": {"h1": ["Real-time Multi-Channel Discovery"]}
    }
    meta = gen.generate("https://pulseradar.dev", crawl_data)
    assert len(meta["title_variants"]) == 3
    assert "og:title" in meta["open_graph"]
    assert "twitter:card" in meta["twitter_card"]
    assert "<title>" in meta["html_code_block"]

def test_image_auditor():
    auditor = ImageSeoAuditor()
    res = auditor.audit("https://pulseradar.dev", MOCK_HTML)
    assert res["total_images"] == 1
    assert res["missing_alt_count"] == 0
    assert res["alt_coverage_percent"] == 100
    assert res["modern_format_percent"] == 100
    assert res["cls_safe_percent"] == 100

def test_keyword_analyzer():
    analyzer = KeywordAndContentAnalyzer()
    res = analyzer.analyze(
        visible_text="What is Generative Engine Optimization? GEO evaluates evidence density, structure, and machine crawlability for AI models.",
        headings={"h1": ["Generative Engine Optimization"], "h2": ["What is GEO?"]},
        raw_html="<h1>Generative Engine Optimization</h1><p>GEO evaluates evidence density.</p>"
    )
    assert res["content_completeness_score"] > 0
    assert len(res["top_keywords"]) > 0

def test_drift_monitor():
    monitor = DriftMonitor()
    crawl_data = {
        "title": {"text": "PulseRadar V1", "length": 13},
        "meta_description": {"text": "V1 description", "length": 14},
        "headings": {"h1_count": 1},
        "json_ld_schemas": [{"@type": "Organization"}],
        "word_count": 500
    }
    snapshot = monitor.create_snapshot(crawl_data, overall_score=80)
    assert snapshot["overall_score"] == 80

    # Test regression detection
    regressed_crawl = {
        "title": {"text": "", "length": 0},
        "meta_description": {"text": "", "length": 0},
        "headings": {"h1_count": 0},
        "json_ld_schemas": [],
        "word_count": 100
    }
    drift = monitor.compare(regressed_crawl, current_score=35, baseline=snapshot)
    assert drift["drift_status"] == "REGRESSION_DETECTED"
    assert len(drift["regressions"]) >= 3
    assert drift["score_delta"] == -45
