"""Generative Engine Optimization (GEO) Analyzer
Evaluates page readiness for citation in AI Search engines:
ChatGPT Search, Perplexity AI, Google Gemini, and Claude.

4-Pillar GEO Signal Stack:
1. Evidence Density (35%): Stats, numbers, named entities, verifiable claims, quotes
2. Structure & Position (25%): Front-loading answers, heading trees, JSON-LD, tables
3. Authority & Attribution (25%): Author entities, organization signals, external citations
4. AI Crawlability (15%): SSR accessibility, machine-readable text, permissive bot access
"""
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup

class GeoOptimizer:
    def evaluate(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        raw_html = crawl_data.get("raw_html", "")
        visible_text = crawl_data.get("visible_text", "")
        word_count = crawl_data.get("word_count", 0)
        headings = crawl_data.get("headings", {})
        schemas = crawl_data.get("json_ld_schemas", [])
        links = crawl_data.get("links", {})
        title_text = crawl_data.get("title", {}).get("text", "")
        meta_desc = crawl_data.get("meta_description", {}).get("text", "")

        soup = BeautifulSoup(raw_html, "html.parser")

        # =====================================================================
        # Pillar 1: Evidence Density (Max 35 points)
        # =====================================================================
        p1_score = 0
        p1_details = []

        # 1.1 Content depth
        if word_count >= 800:
            p1_score += 10
            p1_details.append({"rule": "Content Depth", "status": "PASS", "score": 10, "max": 10, "notes": f"{word_count} words (Deep coverage)"})
        elif word_count >= 400:
            p1_score += 7
            p1_details.append({"rule": "Content Depth", "status": "PASS", "score": 7, "max": 10, "notes": f"{word_count} words (Sufficient coverage)"})
        elif word_count >= 200:
            p1_score += 4
            p1_details.append({"rule": "Content Depth", "status": "PARTIAL", "score": 4, "max": 10, "notes": f"{word_count} words (Minimal depth for LLMs)"})
        else:
            p1_details.append({"rule": "Content Depth", "status": "FAIL", "score": 0, "max": 10, "notes": f"{word_count} words (Thin content, difficult for AI to cite)"})

        # 1.2 Quantitative Evidence & Numbers (LLMs favor verifiable data)
        numbers = re.findall(r"\b(?:\$|€|£)?\d+(?:[\.,]\d+)?%?(?:\+|(?:k|m|b|x)\b)?", visible_text, re.I)
        num_count = len(numbers)
        if num_count >= 15:
            p1_score += 9
            p1_details.append({"rule": "Statistical Density", "status": "PASS", "score": 9, "max": 9, "notes": f"{num_count} statistical metrics & numerical claims found"})
        elif num_count >= 6:
            p1_score += 6
            p1_details.append({"rule": "Statistical Density", "status": "PASS", "score": 6, "max": 9, "notes": f"{num_count} numerical claims detected"})
        elif num_count >= 2:
            p1_score += 3
            p1_details.append({"rule": "Statistical Density", "status": "PARTIAL", "score": 3, "max": 9, "notes": f"{num_count} numbers detected (consider adding concrete benchmarks or metrics)"})
        else:
            p1_details.append({"rule": "Statistical Density", "status": "FAIL", "score": 0, "max": 9, "notes": "No numerical or quantitative facts found"})

        # 1.3 Quotable Sentences & Technical Entities
        # Named entities: capitalized words, technical acronyms (API, SDK, AI, LLM, SaaS, etc.)
        acronyms = set(re.findall(r"\b[A-Z]{2,6}\b", visible_text))
        acronym_count = len(acronyms)
        if acronym_count >= 5:
            p1_score += 8
            p1_details.append({"rule": "Entity & Acronym Density", "status": "PASS", "score": 8, "max": 8, "notes": f"{acronym_count} technical concepts / named entities detected"})
        elif acronym_count >= 2:
            p1_score += 5
            p1_details.append({"rule": "Entity & Acronym Density", "status": "PASS", "score": 5, "max": 8, "notes": f"{acronym_count} named entities detected"})
        else:
            p1_details.append({"rule": "Entity & Acronym Density", "status": "FAIL", "score": 0, "max": 8, "notes": "Sparse domain entity definitions"})

        # 1.4 Structured Lists & Data Tables (AI parsers extract lists into bullet answers)
        has_lists = len(soup.find_all(["ul", "ol", "table"])) > 0
        list_items = len(soup.find_all("li"))
        if list_items >= 8 or soup.find("table"):
            p1_score += 8
            p1_details.append({"rule": "Structured Extractability", "status": "PASS", "score": 8, "max": 8, "notes": f"Rich structured lists/tables ({list_items} items) present"})
        elif has_lists:
            p1_score += 4
            p1_details.append({"rule": "Structured Extractability", "status": "PARTIAL", "score": 4, "max": 8, "notes": "Basic list formatting found"})
        else:
            p1_details.append({"rule": "Structured Extractability", "status": "FAIL", "score": 0, "max": 8, "notes": "No lists or tables found. LLMs struggle to cite dense unstructured prose"})

        # =====================================================================
        # Pillar 2: Structure & Position (Max 25 points)
        # =====================================================================
        p2_score = 0
        p2_details = []

        # 2.1 Front-loaded Answer (Direct Answer in First 200 Words)
        first_200_words = " ".join(visible_text.split()[:200]).lower()
        title_words = set(re.findall(r"\b\w{3,}\b", title_text.lower()))
        front_loaded_matches = [w for w in title_words if w in first_200_words]
        if len(front_loaded_matches) >= 3 or (meta_desc and meta_desc.lower() in first_200_words):
            p2_score += 8
            p2_details.append({"rule": "Front-loaded Answer", "status": "PASS", "score": 8, "max": 8, "notes": "Core topic directly answered and defined in initial 200 words"})
        elif len(front_loaded_matches) >= 1:
            p2_score += 5
            p2_details.append({"rule": "Front-loaded Answer", "status": "PARTIAL", "score": 5, "max": 8, "notes": "Topic partially introduced in first 200 words"})
        else:
            p2_details.append({"rule": "Front-loaded Answer", "status": "FAIL", "score": 0, "max": 8, "notes": "Opening text is vague. LLM crawlers prioritize pages that front-load direct answers"})

        # 2.2 Heading Hierarchy & Question Subheadings
        h1_count = headings.get("h1_count", 0)
        h2_count = headings.get("h2_count", 0)
        h2_texts = headings.get("h2", [])
        question_headings = [h for h in h2_texts if any(h.lower().startswith(q) for q in ["what", "how", "why", "when", "where", "can", "is", "best"]) or "?" in h]
        
        if h1_count == 1 and h2_count >= 2:
            p2_score += 7
            p2_details.append({"rule": "Heading Tree", "status": "PASS", "score": 7, "max": 7, "notes": f"Clean heading hierarchy (1 H1, {h2_count} H2s)"})
        elif h1_count >= 1:
            p2_score += 4
            p2_details.append({"rule": "Heading Tree", "status": "PARTIAL", "score": 4, "max": 7, "notes": "Heading tree exists but needs logical H2 breakdown"})
        else:
            p2_details.append({"rule": "Heading Tree", "status": "FAIL", "score": 0, "max": 7, "notes": "Missing primary heading structure"})

        # Question subheadings bonus (Perplexity and Google AI Overviews target Q&A headings)
        if len(question_headings) >= 1:
            p2_score += 5
            p2_details.append({"rule": "Q&A Headings", "status": "PASS", "score": 5, "max": 5, "notes": f"{len(question_headings)} question-formatted subheadings found"})
        else:
            p2_details.append({"rule": "Q&A Headings", "status": "FAIL", "score": 0, "max": 5, "notes": "No question subheadings (e.g. 'How it works?', 'What is...?') for AI snippet capture"})

        # 2.3 JSON-LD Structured Data
        if len(schemas) > 0:
            schema_types = []
            for s in schemas:
                if isinstance(s, dict):
                    schema_types.append(s.get("@type", "Schema"))
            p2_score += 5
            p2_details.append({"rule": "Schema Knowledge Graph", "status": "PASS", "score": 5, "max": 5, "notes": f"JSON-LD structured data detected: {', '.join(schema_types[:4])}"})
        else:
            p2_details.append({"rule": "Schema Knowledge Graph", "status": "FAIL", "score": 0, "max": 5, "notes": "Missing JSON-LD schema markup. AI engines heavily parse JSON-LD for entity resolution"})

        # =====================================================================
        # Pillar 3: Authority & Attribution (Max 25 points)
        # =====================================================================
        p3_score = 0
        p3_details = []

        # 3.1 Organization or Author Entity
        has_author = bool(soup.find(attrs={"name": re.compile(r"^author$", re.I)}) or soup.find(class_=re.compile(r"author", re.I)))
        has_copyright = bool(re.search(r"©|copyright|\ball rights reserved\b", visible_text, re.I))
        if has_author or has_copyright:
            p3_score += 8
            p3_details.append({"rule": "Author & Entity Identity", "status": "PASS", "score": 8, "max": 8, "notes": "Clear author attribution and entity provenance declared"})
        else:
            p3_details.append({"rule": "Author & Entity Identity", "status": "FAIL", "score": 0, "max": 8, "notes": "Anonymous page. AI models penalize unattributed content on sensitive topics"})

        # 3.2 Outbound Citations & Reference Links
        ext_count = links.get("external_count", 0)
        if ext_count >= 5:
            p3_score += 9
            p3_details.append({"rule": "Outbound Citations", "status": "PASS", "score": 9, "max": 9, "notes": f"{ext_count} outbound references found (High external fact verification)"})
        elif ext_count >= 1:
            p3_score += 5
            p3_details.append({"rule": "Outbound Citations", "status": "PASS", "score": 5, "max": 9, "notes": f"{ext_count} outbound references found"})
        else:
            p3_details.append({"rule": "Outbound Citations", "status": "FAIL", "score": 0, "max": 9, "notes": "Zero outbound citations. AI crawlers favor content that links to sources & documentation"})

        # 3.3 Social Proof & Verified Profiles
        social_domains = ["twitter.com", "x.com", "github.com", "linkedin.com", "youtube.com", "instagram.com"]
        has_social = any(any(sd in link.lower() for sd in social_domains) for link in links.get("external_sample", []))
        if has_social:
            p3_score += 8
            p3_details.append({"rule": "Social Proof Verification", "status": "PASS", "score": 8, "max": 8, "notes": "Connected social profiles & developer channels detected"})
        else:
            p3_details.append({"rule": "Social Proof Verification", "status": "FAIL", "score": 0, "max": 8, "notes": "No verified social/developer profile links found"})

        # =====================================================================
        # Pillar 4: AI Crawlability (Max 15 points)
        # =====================================================================
        p4_score = 0
        p4_details = []

        # 4.1 SSR Machine-readable Content
        if word_count >= 200:
            p4_score += 6
            p4_details.append({"rule": "Server-Side Rendered (SSR) HTML", "status": "PASS", "score": 6, "max": 6, "notes": f"{word_count} words available in initial HTML payload without client JS execution"})
        else:
            p4_details.append({"rule": "Server-Side Rendered (SSR) HTML", "status": "FAIL", "score": 0, "max": 6, "notes": "Low SSR content volume. AI web scrapers often do not execute client JS"})

        # 4.2 Bot-friendly meta tags
        meta_robots = crawl_data.get("robots", {})
        if not meta_robots.get("noindex"):
            p4_score += 5
            p4_details.append({"rule": "AI Indexing Permissions", "status": "PASS", "score": 5, "max": 5, "notes": "Page explicitly allows search & AI indexing"})
        else:
            p4_details.append({"rule": "AI Indexing Permissions", "status": "CRITICAL", "score": 0, "max": 5, "notes": "'noindex' blocks all AI engines from citing this URL"})

        # 4.3 Clean OpenGraph / Twitter Fallbacks
        og = crawl_data.get("open_graph", {})
        if og.get("title") and og.get("description"):
            p4_score += 4
            p4_details.append({"rule": "Card Metadata", "status": "PASS", "score": 4, "max": 4, "notes": "OpenGraph summary tags available for chat snippet generation"})
        else:
            p4_details.append({"rule": "Card Metadata", "status": "PARTIAL", "score": 2, "max": 4, "notes": "Incomplete social snippet tags"})

        total_geo_score = min(100, p1_score + p2_score + p3_score + p4_score)

        # AI Readiness Tier
        if total_geo_score >= 80:
            tier = "PRIME_CITATION_TARGET"
            badge = "High AI Citation Probability"
        elif total_geo_score >= 55:
            tier = "MODERATE_READINESS"
            badge = "Moderate Citation Likelihood"
        else:
            tier = "LOW_READINESS"
            badge = "Needs Optimization for AI Search"

        # Actionable recommendations
        recommendations = []
        if p1_score < 25:
            recommendations.append("Increase evidence density: Add verifiable statistics, quantitative figures, and bulleted takeaways.")
        if p2_score < 18:
            recommendations.append("Front-load the core answer: Provide a crisp 1-2 sentence definition or resolution in the first 150 words.")
        if not schemas:
            recommendations.append("Inject JSON-LD Schema: Add Organization, WebSite, or FAQPage markup to clarify entities to LLMs.")
        if p3_score < 15:
            recommendations.append("Enhance authority: Add author bio with credentials, link to official documentation or source citations.")
        if p4_score < 10:
            recommendations.append("Ensure full SSR: Verify that article text is present in the initial server HTML without client-side rendering.")

        return {
            "overall_score": total_geo_score,
            "readiness_tier": tier,
            "badge": badge,
            "pillars": {
                "evidence_density": {"score": p1_score, "max": 35, "percentage": round((p1_score / 35) * 100), "items": p1_details},
                "structure_and_position": {"score": p2_score, "max": 25, "percentage": round((p2_score / 25) * 100), "items": p2_details},
                "authority_signals": {"score": p3_score, "max": 25, "percentage": round((p3_score / 25) * 100), "items": p3_details},
                "ai_crawlability": {"score": p4_score, "max": 15, "percentage": round((p4_score / 15) * 100), "items": p4_details}
            },
            "recommendations": recommendations
        }
