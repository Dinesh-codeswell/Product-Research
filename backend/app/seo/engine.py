"""Master SEO & GEO Pipeline Orchestrator"""
import asyncio
from typing import Dict, Any, Callable, Optional
from urllib.parse import urlparse

from app.seo.crawler import TechnicalCrawler
from app.seo.geo_optimizer import GeoOptimizer
from app.seo.rendering_gap import RenderingGapAuditor
from app.seo.schema_generator import SchemaGenerator
from app.seo.meta_generator import MetaGenerator
from app.seo.image_auditor import ImageSeoAuditor
from app.seo.keyword_gap import KeywordAndContentAnalyzer
from app.seo.drift_monitor import DriftMonitor
from app.seo.keyword_universe import KeywordUniverseBuilder
from app.seo.content_planner import ContentPlanner
from app.seo.link_integrity import LinkIntegrityAuditor
from app.seo.sitemap_auditor import SitemapAuditor
from app.seo.international_auditor import InternationalAuditor

class SeoAuditEngine:
    def __init__(self):
        self.crawler = TechnicalCrawler()
        self.geo_optimizer = GeoOptimizer()
        self.rendering_auditor = RenderingGapAuditor()
        self.schema_generator = SchemaGenerator()
        self.meta_generator = MetaGenerator()
        self.image_auditor = ImageSeoAuditor()
        self.keyword_analyzer = KeywordAndContentAnalyzer()
        self.drift_monitor = DriftMonitor()
        self.keyword_universe_builder = KeywordUniverseBuilder()
        self.content_planner = ContentPlanner()
        self.link_auditor = LinkIntegrityAuditor()
        self.sitemap_auditor = SitemapAuditor()
        self.international_auditor = InternationalAuditor()

    async def run_audit(
        self,
        url: str,
        audit_type: str = "quick",
        baseline_snapshot: Optional[Dict[str, Any]] = None,
        progress_cb: Optional[Callable[[str, int, str], None]] = None
    ) -> Dict[str, Any]:
        """Executes the complete multi-phase SEO & GEO pipeline."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        def notify(stage: str, pct: int, msg: str):
            if progress_cb:
                progress_cb(stage, pct, msg)

        # -------------------------------------------------------------
        # Phase 1: Technical Crawl
        # -------------------------------------------------------------
        notify("crawling", 15, f"Inspecting server headers, SSL, and HTML payload for {url}...")
        crawl_data = await self.crawler.crawl(url)
        if not crawl_data.get("success"):
            return {
                "success": False,
                "url": url,
                "error": crawl_data.get("error", "Unknown crawler error"),
                "overall_score": 0
            }

        # -------------------------------------------------------------
        # Phase 2: Generative Engine Optimization (GEO)
        # -------------------------------------------------------------
        notify("geo_analysis", 35, "Evaluating 4-Pillar AI Search Citation Readiness (ChatGPT, Perplexity, Gemini)...")
        geo_result = self.geo_optimizer.evaluate(crawl_data)

        # -------------------------------------------------------------
        # Phase 3: JS Rendering & Hydration Gap Test
        # -------------------------------------------------------------
        rendering_result = {"tested": False, "note": "Skipped in quick mode"}
        if audit_type == "full":
            notify("rendering_audit", 55, "Spawning Playwright headless browser to audit client JS hydration gaps...")
            rendering_result = await self.rendering_auditor.audit(url, crawl_data)
        else:
            notify("rendering_audit", 55, "Fast-path SSR check completed...")

        # -------------------------------------------------------------
        # Phase 4: Structured Data & Meta Optimization
        # -------------------------------------------------------------
        notify("metadata_and_schema", 70, "Generating optimized JSON-LD schemas and SERP meta tags...")
        schema_result = self.schema_generator.generate_all(url, crawl_data)
        meta_result = self.meta_generator.generate(url, crawl_data)

        # -------------------------------------------------------------
        # Phase 5: Image SEO & Keyword/Content Analysis
        # -------------------------------------------------------------
        notify("content_and_images", 85, "Auditing image alt text, WebP formats, CLS attributes, and keyword intent...")
        image_result = self.image_auditor.audit(url, crawl_data.get("raw_html", ""))
        keyword_result = self.keyword_analyzer.analyze(
            crawl_data.get("visible_text", ""),
            crawl_data.get("headings", {}),
            crawl_data.get("raw_html", "")
        )

        # -------------------------------------------------------------
        # Phase 5b: Keyword Universe & Editorial Content Plan
        # -------------------------------------------------------------
        notify("keyword_universe", 87, "Building keyword universe (intent classification + topic clusters) & editorial plan...")
        keyword_universe_result = self.keyword_universe_builder.build(
            crawl_data.get("visible_text", ""),
            crawl_data.get("headings", {}),
            crawl_data.get("meta_description", {}).get("text", ""),
        )
        content_plan_result = self.content_planner.build_plan(
            keyword_universe_result,
            existing_content_hints=crawl_data.get("links", {}).get("internal_sample", []),
            domain=crawl_data.get("url", ""),
        )

        # -------------------------------------------------------------
        # Phase 5c: Link Integrity, Sitemap & International Targeting
        # -------------------------------------------------------------
        notify("link_integrity", 89, "Probing sampled links for 404s and redirect chains...")
        link_result = await self.link_auditor.audit(crawl_data)
        sitemap_result = await self.sitemap_auditor.audit(url, crawl_data)
        international_result = self.international_auditor.audit(crawl_data, url)

        # -------------------------------------------------------------
        # Phase 6: AI Search Engine Optimization (GEO) & Strategic SERP Synthesis
        # -------------------------------------------------------------
        from app.engine.ai_planner import AIResearchPlanner
        from app.core.ai_config import AIConfigManager
        ai_planner = AIResearchPlanner()
        active_ai_cfg = AIConfigManager.get_instance().get_config()
        
        notify("ai_synthesis", 92, f"AI Model ({active_ai_cfg.active_model_name}) synthesizing AI citation strategy and SERP recommendations...")
        ai_insights = await ai_planner.generate_seo_strategic_audit(url, crawl_data)

        # -------------------------------------------------------------
        # Phase 7: SEO Drift & Aggregate Scoring
        # -------------------------------------------------------------
        notify("drift_check", 96, "Comparing metrics against baseline snapshot to detect regressions...")
        
        tech_score = crawl_data.get("score", 70)
        geo_score = geo_result.get("overall_score", 50)
        img_score = image_result.get("score", 80)
        content_score = keyword_result.get("content_completeness_score", 60)
        link_score = link_result.get("link_health_score", 100)
        sitemap_score = sitemap_result.get("sitemap_health_score", 0) if sitemap_result.get("success") else 40
        intl_score = international_result.get("international_score", 70)
        
        # On-Page score based on title, meta desc, headings, schemas
        onpage_score = 100
        if not crawl_data.get("title", {}).get("text"):
            onpage_score -= 30
        if not crawl_data.get("meta_description", {}).get("text"):
            onpage_score -= 25
        if crawl_data.get("headings", {}).get("h1_count", 0) != 1:
            onpage_score -= 20
        if schema_result.get("detected_count", 0) == 0:
            onpage_score -= 20
        onpage_score = max(0, min(100, onpage_score))

        # Overall Composite Score (re-weighted to include the new pillars)
        overall_score = round(
            (tech_score * 0.22) +
            (geo_score * 0.26) +
            (onpage_score * 0.17) +
            (img_score * 0.12) +
            (content_score * 0.08) +
            (link_score * 0.07) +
            (sitemap_score * 0.04) +
            (intl_score * 0.04)
        )

        # Drift comparison
        drift_result = self.drift_monitor.compare(crawl_data, overall_score, baseline_snapshot)
        new_snapshot = self.drift_monitor.create_snapshot(crawl_data, overall_score)

        # Executive Synthesis
        summary_lines = [
            f"**SEO & AI Readiness Score:** {overall_score}/100 ({geo_result.get('badge')})",
            "",
            f"- **Technical Health ({tech_score}/100):** Response time {crawl_data.get('response_time_ms')}ms. Status HTTP {crawl_data.get('status_code')}. {len(crawl_data.get('issues', []))} technical issues flagged.",
            f"- **AI Citation Readiness ({geo_score}/100):** Evidence density {geo_result['pillars']['evidence_density']['percentage']}%, structure {geo_result['pillars']['structure_and_position']['percentage']}%, authority {geo_result['pillars']['authority_signals']['percentage']}%.",
            f"- **On-Page & Schema ({onpage_score}/100):** {schema_result.get('detected_count', 0)} JSON-LD schemas detected. Title: {crawl_data.get('title', {}).get('length')} chars. Meta description: {crawl_data.get('meta_description', {}).get('length')} chars.",
            f"- **Image SEO ({img_score}/100):** {image_result.get('total_images')} images analyzed ({image_result.get('alt_coverage_percent')}% alt coverage, {image_result.get('modern_format_percent')}% modern WebP/AVIF format).",
            f"- **Content Depth ({content_score}/100):** {keyword_result.get('word_count')} words with {len(keyword_result.get('top_keywords', []))} extracted focus entities."
        ]
        if rendering_result.get("tested") and rendering_result.get("risk_level") == "HIGH":
            summary_lines.append(f"- **Rendering Warning:** High JS Hydration Gap detected (+{rendering_result.get('words_difference')} words post-hydration). Pre-render content server-side to maximize crawler reach.")
        if link_result.get("broken_count"):
            summary_lines.append(f"- **Link Health ({link_score}/100):** {link_result['broken_count']} broken of {link_result['checked']} sampled links ({link_result['broken_rate'] * 100:.0f}% broken rate).")
        else:
            summary_lines.append(f"- **Link Health ({link_score}/100):** {link_result['checked']} sampled links, zero broken.")
        sitemap_line = (
            f"- **Sitemap ({sitemap_score}/100):** {sitemap_result.get('url_count', 0)} URLs indexed in sitemap."
            if sitemap_result.get("success")
            else "- **Sitemap:** No XML sitemap found — generate one and reference it in robots.txt."
        )
        summary_lines.append(sitemap_line)

        notify("completed", 100, f"SEO audit completed! Overall score: {overall_score}/100")

        return {
            "success": True,
            "url": url,
            "domain": urlparse(url).netloc,
            "audit_type": audit_type,
            "scores": {
                "overall": overall_score,
                "technical": tech_score,
                "geo_readiness": geo_score,
                "onpage": onpage_score,
                "image": img_score,
                "content_completeness": content_score,
                "link_integrity": link_score,
                "sitemap": sitemap_score,
                "international": intl_score
            },
            "executive_summary": "\n".join(summary_lines),
            "technical": crawl_data,
            "geo": geo_result,
            "rendering": rendering_result,
            "schemas": schema_result,
            "meta": meta_result,
            "images": image_result,
            "keywords": keyword_result,
            "keyword_universe": keyword_universe_result,
            "content_plan": content_plan_result,
            "link_integrity": link_result,
            "sitemap": {k: v for k, v in sitemap_result.items() if k != "xml"},
            "international": international_result,
            "drift": drift_result,
            "new_snapshot": new_snapshot,
            "ai_insights": ai_insights
        }
