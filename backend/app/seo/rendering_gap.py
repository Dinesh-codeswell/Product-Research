"""Playwright JS Rendering Gap Auditor
Compares initial Server-Side Rendered (SSR) HTML against
full client-side JavaScript rendered DOM to identify content
invisible to search crawlers and AI bots with strict JS budgets.
"""
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class RenderingGapAuditor:
    async def audit(self, url: str, ssr_crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        ssr_word_count = ssr_crawl_data.get("word_count", 0)
        ssr_title = ssr_crawl_data.get("title", {}).get("text", "")
        ssr_desc = ssr_crawl_data.get("meta_description", {}).get("text", "")
        ssr_h1_count = ssr_crawl_data.get("headings", {}).get("h1_count", 0)
        ssr_schemas_count = len(ssr_crawl_data.get("json_ld_schemas", []))

        csr_title = ""
        csr_desc = ""
        csr_word_count = 0
        csr_h1_count = 0
        csr_schemas_count = 0
        csr_images_count = 0
        playwright_ok = False
        error_msg = None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
                await page.goto(url, wait_until="networkidle", timeout=20000)
                rendered_html = await page.content()
                await browser.close()

                # Parse rendered DOM
                soup = BeautifulSoup(rendered_html, "html.parser")
                t_tag = soup.find("title")
                csr_title = t_tag.get_text(strip=True) if t_tag else ""

                d_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
                csr_desc = d_tag.get("content", "").strip() if d_tag else ""

                csr_h1_count = len(soup.find_all("h1"))
                csr_schemas_count = len(soup.find_all("script", type="application/ld+json"))
                csr_images_count = len(soup.find_all("img"))

                for s in soup(["script", "style", "noscript", "svg"]):
                    s.decompose()
                csr_text = soup.get_text(separator=" ", strip=True)
                csr_word_count = len(re.findall(r"\b\w+\b", csr_text))
                playwright_ok = True

        except Exception as e:
            error_msg = str(e)
            playwright_ok = False

        if not playwright_ok:
            return {
                "tested": False,
                "note": f"Playwright rendering test skipped or timed out ({error_msg}). SSR baseline intact.",
                "rendering_mode": "UNKNOWN",
                "ssr_word_count": ssr_word_count,
                "csr_word_count": ssr_word_count,
                "gap_ratio": 1.0,
                "risk_level": "LOW",
                "findings": []
            }

        # Calculate Gap Metrics
        words_difference = csr_word_count - ssr_word_count
        word_growth_ratio = (csr_word_count / max(1, ssr_word_count))

        findings = []
        risk_level = "LOW"
        rendering_mode = "SSR_OR_STATIC"

        if words_difference > 300 and word_growth_ratio >= 2.0:
            rendering_mode = "CLIENT_SIDE_HYDRATED"
            risk_level = "HIGH"
            findings.append({
                "severity": "CRITICAL",
                "title": "Severe JS Hydration Gap",
                "description": f"Over {words_difference} words are only available after client JavaScript executes. Crawlers without JS rendering (or with constrained render budgets) will perceive this page as empty or thin."
            })
        elif words_difference > 100:
            rendering_mode = "PARTIAL_HYDRATION"
            risk_level = "MEDIUM"
            findings.append({
                "severity": "MEDIUM",
                "title": "Partial Client Rendering",
                "description": f"Page gains {words_difference} words after JS executes. Key dynamic elements should be pre-rendered server-side for maximum indexability."
            })
        else:
            findings.append({
                "severity": "INFO",
                "title": "Clean Server-Side Rendering",
                "description": "Content is fully available in the initial server HTML payload. Excellent crawlability for all search engines and AI agents."
            })

        # Check metadata gaps
        if not ssr_title and csr_title:
            findings.append({
                "severity": "CRITICAL",
                "title": "Title Injected via Client JS",
                "description": "Page title is missing in raw server HTML and only populated after React/Angular/Vue hydration."
            })

        if not ssr_desc and csr_desc:
            findings.append({
                "severity": "HIGH",
                "title": "Meta Description Injected via Client JS",
                "description": "Meta description is absent from SSR payload, which can cause Google to fall back to random text snippets in SERP."
            })

        if ssr_h1_count == 0 and csr_h1_count > 0:
            findings.append({
                "severity": "HIGH",
                "title": "H1 Heading Missing in SSR",
                "description": "H1 heading is injected dynamically, weakening primary keyword topical signals."
            })

        if ssr_schemas_count == 0 and csr_schemas_count > 0:
            findings.append({
                "severity": "MEDIUM",
                "title": "JSON-LD Schemas Injected on Client",
                "description": "Schema markup is added via DOM injection rather than native server response."
            })

        return {
            "tested": True,
            "rendering_mode": rendering_mode,
            "risk_level": risk_level,
            "ssr": {
                "word_count": ssr_word_count,
                "title": ssr_title,
                "meta_description": ssr_desc,
                "h1_count": ssr_h1_count,
                "schema_count": ssr_schemas_count
            },
            "csr": {
                "word_count": csr_word_count,
                "title": csr_title,
                "meta_description": csr_desc,
                "h1_count": csr_h1_count,
                "schema_count": csr_schemas_count,
                "images_count": csr_images_count
            },
            "words_difference": words_difference,
            "word_growth_ratio": round(word_growth_ratio, 2),
            "findings": findings
        }
