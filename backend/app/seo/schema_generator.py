"""JSON-LD Schema Markup Generator & Structured Data Validator"""
import json
from typing import Dict, Any, List
from urllib.parse import urlparse

class SchemaGenerator:
    def generate_all(self, url: str, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        parsed = urlparse(url)
        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{domain}"
        path = parsed.path

        title = crawl_data.get("title", {}).get("text", "") or domain
        desc = crawl_data.get("meta_description", {}).get("text", "") or f"Official website and resources for {domain}"
        og = crawl_data.get("open_graph", {})
        image_url = og.get("image") or f"{base_url}/og-image.png"

        headings = crawl_data.get("headings", {})
        h1 = headings.get("h1", [title])[0] if headings.get("h1") else title
        h2_list = headings.get("h2", [])

        # Find social profile links from crawl
        external_links = crawl_data.get("links", {}).get("external_sample", [])
        social_domains = ["twitter.com", "x.com", "github.com", "linkedin.com", "youtube.com", "facebook.com"]
        same_as_links = [l for l in external_links if any(sd in l.lower() for sd in social_domains)][:8]

        # 1. WebSite Schema
        website_schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": title.split("—")[0].split("-")[0].split("|")[0].strip(),
            "url": base_url,
            "description": desc,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{base_url}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        }

        # 2. Organization Schema
        org_name = domain.split(".")[0].title()
        organization_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": org_name,
            "url": base_url,
            "logo": image_url,
            "description": desc,
            "sameAs": same_as_links if same_as_links else [
                f"https://twitter.com/{domain.split('.')[0]}",
                f"https://github.com/{domain.split('.')[0]}"
            ]
        }

        # 3. SoftwareApplication / Product Schema
        software_schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": h1,
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "All",
            "description": desc,
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD"
            }
        }

        # 4. Article / WebPage Schema
        webpage_schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "url": url,
            "description": desc,
            "isPartOf": {
                "@type": "WebSite",
                "name": org_name,
                "url": base_url
            }
        }

        # 5. BreadcrumbList Schema
        path_segments = [s for s in path.strip("/").split("/") if s]
        breadcrumbs_elements = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": base_url
            }
        ]
        curr_path = base_url
        for idx, seg in enumerate(path_segments, start=2):
            curr_path += f"/{seg}"
            clean_name = seg.replace("-", " ").replace("_", " ").title()
            breadcrumbs_elements.append({
                "@type": "ListItem",
                "position": idx,
                "name": clean_name,
                "item": curr_path
            })
        
        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumbs_elements
        }

        # 6. FAQPage Schema (if question headings exist)
        faq_questions = [h for h in h2_list if "?" in h or any(h.lower().startswith(q) for q in ["what", "how", "why", "can", "is", "where"])]
        faq_elements = []
        for q in faq_questions[:5]:
            faq_elements.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Comprehensive information and guide answering: {q}. See official documentation at {url}."
                }
            })
        
        faq_schema = None
        if faq_elements:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": faq_elements
            }

        # Existing schemas validation
        detected_schemas = crawl_data.get("json_ld_schemas", [])
        validation_findings = []
        if not detected_schemas:
            validation_findings.append({
                "severity": "HIGH",
                "message": "No structured data detected on live page. Search engines and AI engines miss rich snippet badges."
            })
        else:
            for i, s in enumerate(detected_schemas):
                if not isinstance(s, dict):
                    validation_findings.append({"severity": "CRITICAL", "message": f"Schema #{i+1} is not a valid JSON object"})
                    continue
                stype = s.get("@type", "Unknown")
                if not s.get("@context"):
                    validation_findings.append({"severity": "HIGH", "message": f"Schema {stype} is missing '@context': 'https://schema.org'"})
                if not s.get("name") and not s.get("headline"):
                    validation_findings.append({"severity": "MEDIUM", "message": f"Schema {stype} is missing a descriptive 'name' or 'headline'"})

        return {
            "detected_count": len(detected_schemas),
            "detected_schemas": detected_schemas,
            "validation_findings": validation_findings,
            "generated_templates": {
                "website": website_schema,
                "organization": organization_schema,
                "software_application": software_schema,
                "webpage": webpage_schema,
                "breadcrumb": breadcrumb_schema,
                "faq": faq_schema
            },
            "html_snippet_sample": f'<script type="application/ld+json">\n{json.dumps(organization_schema, indent=2)}\n</script>'
        }
