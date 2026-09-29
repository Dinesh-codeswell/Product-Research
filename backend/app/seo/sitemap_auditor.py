"""Sitemap Auditor — XML Sitemap Structure, Freshness & Coverage
(notfair `sitemap-audit` pattern)

Fetches /sitemap.xml (and common variants), validates XML structure, checks
URL validity, lastmod freshness, sitemap-index nesting, and cross-references
the crawled page so coverage gaps become visible.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

SITEMAP_CANDIDATES = [
    "sitemap.xml",
    "sitemap_index.xml",
    "sitemap-index.xml",
    "wp-sitemap.xml",
]


class SitemapAuditor:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    # ------------------------------------------------------------------
    async def _fetch(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        try:
            resp = await client.get(url)
            if resp.status_code == 200 and ("<urlset" in resp.text[:500] or "<sitemapindex" in resp.text[:500]):
                return resp.text
        except Exception as e:
            logger.debug(f"Sitemap fetch failed {url}: {e}")
        return None

    # ------------------------------------------------------------------
    async def audit(self, url: str, crawl_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        origin = f"{parsed.scheme}://{parsed.netloc}"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            # Locate sitemap: robots.txt directive, then common paths
            sitemap_url = None
            robots_txt = None
            try:
                r_resp = await client.get(f"{origin}/robots.txt")
                if r_resp.status_code == 200:
                    robots_txt = r_resp.text
                    for line in robots_txt.splitlines():
                        if line.lower().startswith("sitemap:"):
                            candidate = line.split(":", 1)[1].strip()
                            if candidate.startswith("http"):
                                sitemap_url = candidate
                                break
            except Exception:
                pass

            xml = None
            if sitemap_url:
                xml = await self._fetch(client, sitemap_url)

            if xml is None:
                for candidate in SITEMAP_CANDIDATES:
                    probe_url = urljoin(origin + "/", candidate)
                    xml = await self._fetch(client, probe_url)
                    if xml is not None:
                        sitemap_url = probe_url
                        break

        result: Dict[str, Any] = {
            "success": False,
            "sitemap_url": sitemap_url,
            "robots_declares_sitemap": any(
                line.lower().startswith("sitemap:") for line in (robots_txt or "").splitlines()
            ),
            "url_count": 0,
            "url_count_score": 0,
            "freshness_score": 50,
            "structure_score": 0,
            "sitemap_health_score": 0,
            "issues": [],
        }

        if xml is None:
            result["issues"].append({
                "severity": "HIGH",
                "field": "Sitemap",
                "message": "No XML sitemap found at common paths (/sitemap.xml, /sitemap_index.xml) or robots.txt directive.",
            })
            result["sitemap_health_score"] = 0
            result["note"] = "Sitemaps help search engines discover pages; generate one and reference it in robots.txt."
            return result

        result["success"] = True

        # ---- Parse structure ----
        is_index = "<sitemapindex" in xml[:500]
        entries: List[Dict[str, Any]] = []
        parse_error = None
        try:
            root = ElementTree.fromstring(xml.encode() if isinstance(xml, str) else xml)
            if is_index:
                for sm in root.findall("sm:sitemap", NS):
                    loc = sm.find("sm:loc", NS)
                    lastmod = sm.find("sm:lastmod", NS)
                    entries.append({
                        "loc": (loc.text or "").strip() if loc is not None else "",
                        "lastmod": (lastmod.text or "").strip() if lastmod is not None else "",
                        "kind": "sub_sitemap",
                    })
            else:
                for u in root.findall("sm:url", NS):
                    loc = u.find("sm:loc", NS)
                    lastmod = u.find("sm:lastmod", NS)
                    entries.append({
                        "loc": (loc.text or "").strip() if loc is not None else "",
                        "lastmod": (lastmod.text or "").strip() if lastmod is not None else "",
                        "kind": "url",
                    })
        except ElementTree.ParseError as pe:
            parse_error = str(pe)

        if parse_error:
            result["issues"].append({"severity": "HIGH", "field": "Sitemap XML", "message": f"Malformed XML: {parse_error[:200]}"})
            result["structure_score"] = 0
            result["sitemap_health_score"] = 20
            return result

        result["is_sitemap_index"] = is_index
        result["entry_count"] = len(entries)
        result["url_count"] = len([e for e in entries if e["kind"] == "url"])

        # ---- URL validity ----
        invalid_urls = [
            e["loc"] for e in entries
            if not e["loc"].startswith(("http://", "https://"))
        ]
        non_canonical_hosts = [
            e["loc"] for e in entries
            if urlparse(e["loc"]).netloc and urlparse(e["loc"]).netloc.lower() != parsed.netloc.lower()
        ]
        if invalid_urls:
            result["issues"].append({
                "severity": "MEDIUM",
                "field": "Sitemap URLs",
                "message": f"{len(invalid_urls)} entries are not absolute http(s) URLs.",
            })
        if non_canonical_hosts:
            result["issues"].append({
                "severity": "MEDIUM",
                "field": "Sitemap URLs",
                "message": f"{len(non_canonical_hosts)} entries point to a different host than {parsed.netloc} (cross-host URLs split indexing signals).",
            })

        # ---- Freshness ----
        now = datetime.utcnow()
        dated = []
        stale_count = 0
        fresh_count = 0
        for e in entries:
            lm = e.get("lastmod", "")
            if not lm:
                continue
            try:
                dt = datetime.fromisoformat(lm.replace("Z", "+00:00")).replace(tzinfo=None)
                dated.append(dt)
                age_days = (now - dt).days
                if 0 <= age_days <= 30:
                    fresh_count += 1
                elif age_days > 365:
                    stale_count += 1
            except Exception:
                pass

        if dated:
            newest = max(dated)
            age_newest_days = (now - newest).days
            result["newest_lastmod"] = newest.strftime("%Y-%m-%d")
            result["newest_lastmod_age_days"] = age_newest_days
            if age_newest_days <= 7:
                result["freshness_score"] = 100
            elif age_newest_days <= 30:
                result["freshness_score"] = 80
            elif age_newest_days <= 90:
                result["freshness_score"] = 55
            else:
                result["freshness_score"] = 25
                result["issues"].append({
                    "severity": "MEDIUM",
                    "field": "Sitemap Freshness",
                    "message": f"Newest lastmod is {age_newest_days} days old — search engines may deprioritize crawl.",
                })
        else:
            result["freshness_score"] = 40
            result["issues"].append({
                "severity": "LOW",
                "field": "Sitemap Freshness",
                "message": "No <lastmod> dates present — add them to help crawlers prioritize.",
            })

        # ---- Scoring ----
        count_score = 100 if 1 <= result["url_count"] <= 50_000 else (60 if result["url_count"] > 0 else 0)
        if result["url_count"] > 50_000:
            result["issues"].append({
                "severity": "MEDIUM",
                "field": "Sitemap Size",
                "message": "Sitemap exceeds the 50,000-URL limit per file — split with a sitemap index.",
            })
        structure_penalty = min(40, len(invalid_urls) * 5 + len(non_canonical_hosts) * 3)
        result["url_count_score"] = count_score
        result["structure_score"] = max(0, 100 - structure_penalty)
        result["sitemap_health_score"] = round(
            count_score * 0.35 + result["structure_score"] * 0.35 + result["freshness_score"] * 0.30
        )

        # ---- Coverage cross-reference: is the audited page in the sitemap? ----
        if crawl_data and crawl_data.get("url"):
            crawled_path = urlparse(crawl_data["url"]).path.rstrip("/") or "/"
            sitemap_paths = {urlparse(e["loc"]).path.rstrip("/") or "/" for e in entries if e["loc"]}
            result["crawled_page_in_sitemap"] = crawled_path in sitemap_paths
            if not result["crawled_page_in_sitemap"]:
                result["issues"].append({
                    "severity": "LOW",
                    "field": "Sitemap Coverage",
                    "message": f"Audited page path '{crawled_path}' was not found in the sitemap.",
                })

        result["sample_urls"] = [e["loc"] for e in entries[:15] if e["loc"]]
        return result
