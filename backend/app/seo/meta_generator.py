"""Meta Tags, Social OpenGraph & SERP Preview Optimizer"""
from typing import Dict, Any, List
from urllib.parse import urlparse

class MetaGenerator:
    def generate(self, url: str, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        parsed = urlparse(url)
        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{domain}"

        current_title = crawl_data.get("title", {}).get("text", "") or domain
        current_desc = crawl_data.get("meta_description", {}).get("text", "")
        og = crawl_data.get("open_graph", {})
        image_url = og.get("image") or f"{base_url}/og-image.png"

        headings = crawl_data.get("headings", {})
        h1 = headings.get("h1", [current_title])[0] if headings.get("h1") else current_title
        brand_name = domain.split(".")[0].title()

        # Clean core topic
        topic = h1.replace("Home", "").replace("Welcome", "").strip() or brand_name

        # 3 Title Variants
        title_options = [
            {
                "variant": "Brand + Value Proposition",
                "title": f"{brand_name} — {topic} | Official Platform"[:60],
                "char_count": len(f"{brand_name} — {topic} | Official Platform"[:60]),
                "status": "PASS",
                "description": "Standard high-authority formula balancing branded search and core capability."
            },
            {
                "variant": "Benefit / Action First",
                "title": f"{topic}: Complete Intelligence & Specs — {brand_name}"[:60],
                "char_count": len(f"{topic}: Complete Intelligence & Specs — {brand_name}"[:60]),
                "status": "PASS",
                "description": "Optimized for search click-through rate (CTR) by leading with user value."
            },
            {
                "variant": "Keyword & Entity Focused",
                "title": f"Verified {topic} Overview, Architecture & Guide ({brand_name})"[:60],
                "char_count": len(f"Verified {topic} Overview, Architecture & Guide ({brand_name})"[:60]),
                "status": "PASS",
                "description": "Targets broad informational and commercial search intent."
            }
        ]

        # 160-Character Optimized Meta Description
        if current_desc and 70 <= len(current_desc) <= 160:
            suggested_desc = current_desc
        else:
            suggested_desc = f"Discover {topic} with {brand_name}. Explore verified data, automated intelligence, architecture, and live customer insights. Learn more."
            if len(suggested_desc) > 160:
                suggested_desc = suggested_desc[:157] + "..."

        # Social Cards
        og_tags = {
            "og:title": title_options[0]["title"],
            "og:description": suggested_desc,
            "og:url": url,
            "og:site_name": brand_name,
            "og:type": "website",
            "og:image": image_url
        }

        twitter_tags = {
            "twitter:card": "summary_large_image",
            "twitter:title": title_options[0]["title"],
            "twitter:description": suggested_desc,
            "twitter:image": image_url
        }

        # Ready-to-paste HTML snippet
        html_code = (
            f"<!-- Primary Meta Tags -->\n"
            f"<title>{title_options[0]['title']}</title>\n"
            f'<meta name="title" content="{title_options[0]["title"]}">\n'
            f'<meta name="description" content="{suggested_desc}">\n'
            f'<link rel="canonical" href="{url}">\n\n'
            f"<!-- Open Graph / Facebook -->\n"
            f'<meta property="og:type" content="website">\n'
            f'<meta property="og:url" content="{url}">\n'
            f'<meta property="og:title" content="{og_tags["og:title"]}">\n'
            f'<meta property="og:description" content="{og_tags["og:description"]}">\n'
            f'<meta property="og:image" content="{og_tags["og:image"]}">\n\n'
            f"<!-- Twitter -->\n"
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:url" content="{url}">\n'
            f'<meta name="twitter:title" content="{twitter_tags["twitter:title"]}">\n'
            f'<meta name="twitter:description" content="{twitter_tags["twitter:description"]}">\n'
            f'<meta name="twitter:image" content="{twitter_tags["twitter:image"]}">\n'
        )

        return {
            "title_variants": title_options,
            "recommended_description": {
                "text": suggested_desc,
                "length": len(suggested_desc),
                "status": "PASS" if len(suggested_desc) <= 160 else "WARN"
            },
            "open_graph": og_tags,
            "twitter_card": twitter_tags,
            "serp_simulation": {
                "title": title_options[0]["title"],
                "url": url,
                "domain": domain,
                "description": suggested_desc,
                "is_truncated": len(title_options[0]["title"]) > 60
            },
            "html_code_block": html_code
        }
