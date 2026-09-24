"""Technical SEO Crawler & HTML Inspector"""
import time
import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 PulseRadarSEOBot/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

class TechnicalCrawler:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def crawl(self, url: str) -> Dict[str, Any]:
        """Performs a deep technical inspection of a given URL."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed_origin = urlparse(url)
        origin_domain = parsed_origin.netloc.lower()

        start_time = time.time()
        redirect_chain = []
        status_code = 0
        final_url = url
        raw_html = ""
        response_headers = {}
        error_msg = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=HEADERS) as client:
                resp = await client.get(url)
                status_code = resp.status_code
                final_url = str(resp.url)
                raw_html = resp.text
                response_headers = dict(resp.headers)
                if resp.history:
                    redirect_chain = [str(r.url) for r in resp.history] + [final_url]
        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "url": url,
                "status_code": status_code,
                "error": error_msg,
                "response_time_ms": round((time.time() - start_time) * 1000),
                "score": 0,
                "issues": [{"severity": "CRITICAL", "message": f"Connection failed: {error_msg}"}]
            }

        elapsed_ms = round((time.time() - start_time) * 1000)
        content_length = len(raw_html)

        # Parse HTML
        soup = BeautifulSoup(raw_html, "lxml" if "lxml" in BeautifulSoup.__dict__ else "html.parser")

        # 1. Title Tag
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        title_len = len(title_text)

        # 2. Meta Description
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        meta_desc_len = len(meta_desc)

        # 3. Canonical Tag
        canonical_tag = soup.find("link", rel=lambda x: x and "canonical" in x.lower())
        canonical_href = canonical_tag.get("href", "").strip() if canonical_tag else ""
        is_canonical_self = False
        if canonical_href:
            parsed_canon = urlparse(canonical_href)
            parsed_final = urlparse(final_url)
            is_canonical_self = (parsed_canon.netloc == parsed_final.netloc and parsed_canon.path.rstrip('/') == parsed_final.path.rstrip('/'))

        # 4. Robots Directives
        robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_content = robots_tag.get("content", "").strip() if robots_tag else ""
        is_noindex = "noindex" in robots_content.lower()
        is_nofollow = "nofollow" in robots_content.lower()

        # 5. Headings Tree
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

        # 6. OpenGraph & Twitter Cards
        og_data = {}
        for m in soup.find_all("meta", property=re.compile(r"^og:", re.I)):
            prop = m.get("property", "").lower()
            val = m.get("content", "").strip()
            if prop and val:
                og_data[prop.replace("og:", "")] = val

        twitter_data = {}
        for m in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:", re.I)}):
            prop = m.get("name", "").lower()
            val = m.get("content", "").strip()
            if prop and val:
                twitter_data[prop.replace("twitter:", "")] = val

        # 7. JSON-LD Structured Data
        json_ld_schemas = []
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                if s.string:
                    data = json.loads(s.string)
                    json_ld_schemas.append(data)
            except Exception:
                pass

        # 8. Links Audit
        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full_link = urljoin(final_url, href)
            link_domain = urlparse(full_link).netloc.lower()
            if link_domain == origin_domain:
                internal_links.append(full_link)
            else:
                external_links.append(full_link)

        # 9. Text Content Extraction
        for script_or_style in soup(["script", "style", "noscript", "svg"]):
            script_or_style.decompose()
        visible_text = soup.get_text(separator=" ", strip=True)
        words = [w for w in re.findall(r"\b\w+\b", visible_text)]
        word_count = len(words)

        # 10. Technical Scoring & Issue Detection
        score = 100
        issues = []
        passes = []

        # Status Code check
        if status_code == 200:
            passes.append("HTTP 200 OK received")
        elif status_code in (301, 302, 307, 308):
            score -= 10
            issues.append({"severity": "MEDIUM", "field": "Status Code", "message": f"Redirect detected (HTTP {status_code}) -> {final_url}"})
        else:
            score -= 50
            issues.append({"severity": "CRITICAL", "field": "Status Code", "message": f"Returned error HTTP status {status_code}"})

        # Title check
        if not title_text:
            score -= 25
            issues.append({"severity": "CRITICAL", "field": "Title", "message": "Missing <title> tag on page"})
        elif title_len < 30:
            score -= 8
            issues.append({"severity": "LOW", "field": "Title", "message": f"Title tag is short ({title_len} chars, recommended 45-60)"})
        elif title_len > 65:
            score -= 8
            issues.append({"severity": "MEDIUM", "field": "Title", "message": f"Title tag will truncate on Google SERP ({title_len} chars, max 60)"})
        else:
            passes.append(f"Title tag length optimal ({title_len} chars)")

        # Meta description check
        if not meta_desc:
            score -= 20
            issues.append({"severity": "HIGH", "field": "Meta Description", "message": "Missing meta description tag"})
        elif meta_desc_len < 70:
            score -= 6
            issues.append({"severity": "LOW", "field": "Meta Description", "message": f"Meta description is short ({meta_desc_len} chars, recommended 120-160)"})
        elif meta_desc_len > 165:
            score -= 6
            issues.append({"severity": "MEDIUM", "field": "Meta Description", "message": f"Meta description exceeds SERP snippet limit ({meta_desc_len} chars, max 160)"})
        else:
            passes.append(f"Meta description length optimal ({meta_desc_len} chars)")

        # Headings check
        if len(h1_tags) == 0:
            score -= 15
            issues.append({"severity": "HIGH", "field": "H1 Heading", "message": "No <h1> heading found on the page"})
        elif len(h1_tags) > 1:
            score -= 10
            issues.append({"severity": "MEDIUM", "field": "H1 Heading", "message": f"Multiple <h1> headings found ({len(h1_tags)}). Search engines prefer exactly one primary H1"})
        else:
            passes.append(f"Primary H1 heading present: \"{h1_tags[0][:50]}\"")

        # Canonical check
        if not canonical_href:
            score -= 10
            issues.append({"severity": "MEDIUM", "field": "Canonical", "message": "Missing rel='canonical' tag"})
        else:
            passes.append("rel='canonical' tag properly declared")

        # Robots noindex check
        if is_noindex:
            score -= 40
            issues.append({"severity": "CRITICAL", "field": "Robots Directives", "message": "Page contains 'noindex' directive, blocking Google & search engines"})

        # Structured data check
        if len(json_ld_schemas) == 0:
            score -= 15
            issues.append({"severity": "MEDIUM", "field": "Structured Data", "message": "No JSON-LD structured data detected"})
        else:
            passes.append(f"{len(json_ld_schemas)} JSON-LD schema blocks detected")

        # OpenGraph check
        if not og_data.get("title") or not og_data.get("image"):
            score -= 8
            issues.append({"severity": "LOW", "field": "Open Graph", "message": "Incomplete Open Graph tags for social & card sharing"})
        else:
            passes.append("Open Graph social sharing tags configured")

        # Response Time check
        if elapsed_ms > 2000:
            score -= 15
            issues.append({"severity": "HIGH", "field": "Server Speed", "message": f"Slow initial server response: {elapsed_ms}ms (>2000ms)"})
        elif elapsed_ms > 800:
            score -= 5
            issues.append({"severity": "LOW", "field": "Server Speed", "message": f"Moderate server response: {elapsed_ms}ms (>800ms)"})
        else:
            passes.append(f"Fast initial response time: {elapsed_ms}ms")

        # Content volume check
        if word_count < 150:
            score -= 15
            issues.append({"severity": "HIGH", "field": "Content Depth", "message": f"Thin content detected ({word_count} words). Pages under 200 words struggle to rank"})
        else:
            passes.append(f"Healthy content volume ({word_count} words)")

        final_score = max(0, min(100, score))

        return {
            "success": True,
            "url": final_url,
            "status_code": status_code,
            "response_time_ms": elapsed_ms,
            "content_length_bytes": content_length,
            "content_type": response_headers.get("content-type", ""),
            "server": response_headers.get("server", ""),
            "title": {
                "text": title_text,
                "length": title_len,
                "status": "PASS" if 30 <= title_len <= 65 else ("FAIL" if not title_text else "WARN")
            },
            "meta_description": {
                "text": meta_desc,
                "length": meta_desc_len,
                "status": "PASS" if 70 <= meta_desc_len <= 165 else ("FAIL" if not meta_desc else "WARN")
            },
            "canonical": {
                "url": canonical_href,
                "is_self": is_canonical_self,
                "present": bool(canonical_href)
            },
            "robots": {
                "content": robots_content,
                "noindex": is_noindex,
                "nofollow": is_nofollow
            },
            "headings": {
                "h1": h1_tags,
                "h2": h2_tags[:10],
                "h3": h3_tags[:10],
                "h1_count": len(h1_tags),
                "h2_count": len(h2_tags),
                "h3_count": len(h3_tags)
            },
            "open_graph": og_data,
            "twitter_card": twitter_data,
            "json_ld_schemas": json_ld_schemas,
            "links": {
                "internal_count": len(internal_links),
                "external_count": len(external_links),
                "internal_sample": list(set(internal_links))[:15],
                "external_sample": list(set(external_links))[:10]
            },
            "word_count": word_count,
            "score": final_score,
            "issues": issues,
            "passes": passes,
            "raw_html": raw_html,
            "visible_text": visible_text
        }
