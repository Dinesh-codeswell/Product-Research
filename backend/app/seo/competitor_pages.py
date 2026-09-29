"""Competitor Pages Analyzer — SERP Brief & Content-Gap Comparison
(notfair `competitor-pages` pattern)

Fetches the pages currently competing for a target keyword (via the DDG
search backend already used by the Reddit channel), extracts their headings,
content depth, and structured-data usage, then produces a practical brief:
what to cover, what to beat, and which evidence types to include.
"""
import asyncio
import logging
import re
from collections import Counter
from typing import Dict, Any, List, Optional

import httpx
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

from app.seo.keyword_gap import STOP_WORDS

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 PulseRadarSEO/1.0"


class CompetitorPagesAnalyzer:
    def __init__(self, timeout: float = 10.0, max_competitors: int = 4):
        self.timeout = timeout
        self.max_competitors = max_competitors

    # ------------------------------------------------------------------
    def _search_serps(self, keyword: str) -> List[Dict[str, str]]:
        if DDGS is None:
            return []
        try:
            results = list(DDGS().text(f"{keyword}", max_results=self.max_competitors * 2))
            out = []
            seen = set()
            for r in results:
                url = r.get("href", "")
                if not url.startswith(("http://", "https://")) or url in seen:
                    continue
                seen.add(url)
                out.append({"url": url, "title": r.get("title", ""), "snippet": r.get("body", "")})
                if len(out) >= self.max_competitors:
                    break
            return out
        except Exception as e:
            logger.debug(f"SERP search failed for '{keyword}': {e}")
            return []

    # ------------------------------------------------------------------
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        try:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", "html"):
                return resp.text
        except Exception as e:
            logger.debug(f"Competitor fetch failed {url}: {e}")
        return None

    @staticmethod
    def _analyze_html(html: str, url: str, title: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
        text = soup.get_text(" ", strip=True)
        words = re.findall(r"\b\w{3,}\b", text.lower())
        word_count = len(words)

        schemas = len(soup.find_all("script", type="application/ld+json"))
        has_table = soup.find("table") is not None
        has_list = soup.find(["ul", "ol"]) is not None
        has_faq = "faq" in text.lower() or any("faq" in h2.lower() for h2 in h2s)
        numbers = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))

        topics = [
            w for w, c in Counter(w for w in words if w not in STOP_WORDS).most_common(8)
        ]

        return {
            "url": url,
            "title": title[:150],
            "word_count": word_count,
            "h2_count": len(h2s),
            "h2_sample": h2s[:6],
            "h1_count": len(h1s),
            "schema_count": schemas,
            "has_table": has_table,
            "has_list": has_list,
            "has_faq": has_faq,
            "stat_density": numbers,
            "key_topics": topics,
        }

    # ------------------------------------------------------------------
    async def analyze(self, keyword: str, own_domain: Optional[str] = None) -> Dict[str, Any]:
        serp_entries = self._search_serps(keyword)

        competitors: List[Dict[str, Any]] = []
        if serp_entries:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                pages = await asyncio.gather(*(self._fetch_page(client, e["url"]) for e in serp_entries))
            for entry, html in zip(serp_entries, pages):
                if html is None:
                    competitors.append({
                        "url": entry["url"], "title": entry["title"],
                        "fetch_failed": True, "word_count": 0,
                        "snippet": entry.get("snippet", "")[:200],
                    })
                    continue
                analysis = self._analyze_html(html, entry["url"], entry["title"])
                analysis["snippet"] = entry.get("snippet", "")[:200]
                competitors.append(analysis)

        analyzed = [c for c in competitors if not c.get("fetch_failed")]

        # ---- Synthesize the brief ----
        avg_words = round(sum(c["word_count"] for c in analyzed) / len(analyzed)) if analyzed else 0
        avg_h2 = round(sum(c["h2_count"] for c in analyzed) / len(analyzed)) if analyzed else 0
        schema_adoption = round(100 * sum(1 for c in analyzed if c["schema_count"] > 0) / len(analyzed)) if analyzed else 0
        table_adoption = round(100 * sum(1 for c in analyzed if c["has_table"]) / len(analyzed)) if analyzed else 0
        faq_adoption = round(100 * sum(1 for c in analyzed if c["has_faq"]) / len(analyzed)) if analyzed else 0

        # Topic gap: topics covered by ≥2 competitors
        topic_counter: Counter = Counter()
        for c in analyzed:
            for t in set(c.get("key_topics", [])):
                topic_counter[t] += 1
        must_cover_topics = [t for t, n in topic_counter.most_common(10) if n >= max(2, len(analyzed) // 2)]

        recommendations = []
        if avg_words:
            recommendations.append(f"Target {max(1200, int(avg_words * 1.2))}+ words (competitors average {avg_words}).")
        if avg_h2:
            recommendations.append(f"Structure with {max(4, avg_h2)}+ H2 sections (competitors average {avg_h2}).")
        if schema_adoption < 100:
            recommendations.append(f"Only {schema_adoption}% of ranking pages ship JSON-LD — a schema-complete page differentiates immediately.")
        if table_adoption < 60:
            recommendations.append("Add a comparison/spec table — most competitors rank without one; it's an easy evidence win.")
        if faq_adoption < 60:
            recommendations.append("Add an FAQ section with FAQPage schema — under-used across this SERP.")
        recommendations.append(f"Must-cover topics (2+ competitors): {', '.join(must_cover_topics[:6]) or 'n/a'}.")

        if own_domain:
            own_present = any(own_domain in c["url"] for c in competitors)
            recommendations.append(
                "Your domain appears in this SERP." if own_present
                else f"Your domain ({own_domain}) is NOT in the top results — the brief above is your entry path."
            )

        return {
            "success": True,
            "keyword": keyword,
            "competitors_found": len(competitors),
            "competitors_analyzed": len(analyzed),
            "competitors": competitors[: self.max_competitors],
            "serp_stats": {
                "avg_word_count": avg_words,
                "avg_h2_sections": avg_h2,
                "schema_adoption_percent": schema_adoption,
                "table_adoption_percent": table_adoption,
                "faq_adoption_percent": faq_adoption,
            },
            "must_cover_topics": must_cover_topics,
            "recommendations": recommendations,
        }
