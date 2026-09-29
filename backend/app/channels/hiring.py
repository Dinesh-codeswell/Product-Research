"""Hiring Signals Channel Adapter — Careers-Page Intelligence (Free, Zero-Auth)

Inspired by last30days' `--hiring-signals`: a company's current job openings
are cited evidence for strategic focus shifts (e.g. "hiring into enterprise
security" → enterprise push). Scrapes public careers pages / job boards for
the given query (company or product name) and infers the focus areas their
hiring appears to signal — never speculating about unreleased roadmaps.
"""
import asyncio
import logging
import re
from collections import Counter
from typing import List, Optional
from urllib.parse import quote_plus

import httpx

from app.channels.base import BaseChannel, ChannelItem
from app.core.config import settings

logger = logging.getLogger(__name__)

# Free, keyless job-board JSON endpoints
REMOTEOK_URL = "https://remoteok.com/api"
WEWORKREMOTE_URL = "https://weworkremotely.com/remote-jobs.rss"

# Focus-area taxonomy mapped from role titles/descriptions
FOCUS_PATTERNS = {
    "enterprise_security": [r"security", r"appsec", r"soc", r"compliance", r"grc", r"pen.?test"],
    "ai_ml": [r"machine learning", r"\bml\b", r"\bai\b", r"llm", r"data scientist", r"deep learning"],
    "infrastructure": [r"sre", r"devops", r"platform engineer", r"kubernetes", r"infra", r"cloud engineer"],
    "customer_success": [r"customer success", r"support engineer", r"onboarding", r"account manage"],
    "sales_gtm": [r"account executive", r"\bsales\b", r"revenue", r"business development", r"\bgrowth\b"],
    "product_expansion": [r"product manager", r"product design", r"\bux\b", r"\bui\b", r"designer"],
    "mobile": [r"ios engineer", r"android engineer", r"react native", r"mobile engineer"],
    "data_platform": [r"data engineer", r"analytics engineer", r"data platform", r"\betl\b", r"\bdbt\b"],
}


class HiringSignalsChannel(BaseChannel):
    name = "hiring"
    display_name = "Hiring Signals"
    category = "business"
    tier = 0
    backends = ["remoteok_api", "offline_seed"]

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    async def check(self) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(REMOTEOK_URL, headers=self._headers())
                if resp.status_code == 200:
                    self.active_backend = "remoteok_api"
                    return "ok", "RemoteOK public job API operational (zero-auth)"
                self.active_backend = "offline_seed"
                return "warn", f"RemoteOK returned HTTP {resp.status_code} (failover: offline seed)"
        except Exception:
            self.active_backend = "offline_seed"
            return "warn", "RemoteOK timed out (failover: offline seed)"

    def _headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PulseRadar/1.0",
            "Accept": "application/json, text/html, */*",
        }

    @staticmethod
    def _infer_focus(text: str) -> List[str]:
        text_lower = text.lower()
        scores = {}
        for focus, patterns in FOCUS_PATTERNS.items():
            score = sum(len(re.findall(p, text_lower)) for p in patterns)
            if score > 0:
                scores[focus] = score
        ranked = [f for f, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]
        return ranked[:3]

    def _job_to_item(self, job: dict, rank: int, query: str) -> Optional[ChannelItem]:
        position = (job.get("position") or job.get("title") or "").strip()
        company = (job.get("company") or job.get("company_name") or "").strip()
        if not position:
            return None

        slug = job.get("slug") or ""
        url = f"https://remoteok.com/remote-jobs/{slug}" if slug else "https://remoteok.com"
        description = re.sub(r"<[^>]+>", " ", job.get("description") or "")
        description = re.sub(r"\s+", " ", description).strip()[:600]
        tags = ", ".join(job.get("tags") or [])[:200]
        salary_min = job.get("salary_min") or 0
        salary_max = job.get("salary_max") or 0

        focus_areas = self._infer_focus(f"{position} {description} {tags}")

        content_parts = [
            f"Open role: {position} at {company or 'hiring company'}",
            description,
        ]
        if tags:
            content_parts.append(f"Skills: {tags}")
        if salary_max:
            content_parts.append(f"Salary band: ${salary_min:,}–${salary_max:,}")
        if focus_areas:
            content_parts.append(f"Focus signals: {', '.join(focus_areas)}")

        engagement = max(90, 220 - rank * 10)

        return ChannelItem(
            external_id=f"hiring_{slug or hash(position)}_{rank}",
            channel="hiring",
            url=url,
            title=f"{company or 'Company'} hiring: {position}",
            content="\n".join(p for p in content_parts if p),
            author=f"@{company.lower().replace(' ', '_')}" if company else "@hiring_team",
            engagement_score=engagement,
            raw_metadata={
                "source": "remoteok_api",
                "company": company,
                "focus_areas": focus_areas,
                "category_hint": "hiring_signal",
            },
        )

    async def search(self, query: str, limit: int = 30, **kwargs) -> List[ChannelItem]:
        items: List[ChannelItem] = []
        query_terms = [t for t in re.findall(r"[a-z0-9]{3,}", query.lower())]

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(REMOTEOK_URL, headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json()
                    # RemoteOK returns a legal notice dict as the first element
                    jobs = [j for j in data if isinstance(j, dict) and j.get("position")]

                    def relevance(j: dict) -> int:
                        hay = f"{j.get('position', '')} {j.get('company', '')} {j.get('description', '')}".lower()
                        return sum(1 for t in query_terms if t in hay)

                    jobs.sort(key=relevance, reverse=True)
                    for rank, job in enumerate(jobs):
                        rel = relevance(job)
                        # Require at least one term match unless we still need fill
                        if rel == 0 and len(items) >= max(3, limit // 3):
                            break
                        item = self._job_to_item(job, rank, query)
                        if item:
                            items.append(item)
                        if len(items) >= limit:
                            break
                else:
                    logger.debug(f"RemoteOK HTTP {resp.status_code}")
        except Exception as e:
            logger.debug(f"RemoteOK search error: {e}")

        if not items:
            items = self._get_fallback_items(query)

        return items[:limit]

    def _get_fallback_items(self, query: str) -> List[ChannelItem]:
        return [
            ChannelItem(
                external_id=f"hiring_seed_1_{hash(query)}",
                channel="hiring",
                url="https://remoteok.com",
                title=f"Hiring activity signals around {query}",
                content=(
                    f"Companies invest headcount where strategy is heading. Current "
                    f"openings connected to {query} act as cited evidence for focus "
                    "shifts — hiring into security, AI, enterprise sales, or customer "
                    "success each tell a different strategic story. This seed entry "
                    "appeared because live job-board probing was unavailable."
                ),
                author="@talent_observer",
                engagement_score=110,
                raw_metadata={"source": "offline_seed"},
            ),
        ]
