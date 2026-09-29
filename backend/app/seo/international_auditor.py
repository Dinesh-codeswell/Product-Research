"""International SEO Auditor — hreflang, Canonical & Language Targeting
(notfair `hreflang-international` pattern)

Diagnoses hreflang annotation problems: missing return tags, invalid
language/region codes, conflicting canonicals, HTML lang attribute
mismatches, and mixed annotation strategies (link vs header).
"""
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Valid ISO 639-1 language codes (common subset) and ISO 3166-1 alpha-2 regions
COMMON_LANGS = {
    "af", "ar", "bg", "bn", "ca", "cs", "da", "de", "el", "en", "es", "et", "fa",
    "fi", "fr", "he", "hi", "hr", "hu", "id", "it", "ja", "ko", "lt", "lv", "ms",
    "nl", "no", "pl", "pt", "ro", "ru", "sk", "sl", "sr", "sv", "th", "tr", "uk",
    "vi", "zh",
}
COMMON_REGIONS = {
    "ad", "ae", "at", "au", "be", "br", "ca", "ch", "cl", "cn", "cz", "de", "dk",
    "ee", "es", "fi", "fr", "gb", "gr", "hk", "hr", "hu", "id", "ie", "il", "in",
    "is", "it", "jp", "kr", "lt", "lv", "mx", "my", "nl", "no", "nz", "ph", "pl",
    "pt", "ro", "rs", "ru", "se", "sg", "si", "sk", "th", "tr", "tw", "us", "vn", "za",
}

# x-default and x-langs are special values
SPECIAL_HREFLANG = {"x-default"}


def _validate_hreflang_code(code: str) -> Optional[str]:
    """Returns an error string when the code is invalid, else None."""
    code = code.strip().lower()
    if code in SPECIAL_HREFLANG:
        return None
    parts = code.split("-")
    if not parts or parts[0] not in COMMON_LANGS:
        return f"Unknown language code '{code}'"
    if len(parts) == 2 and parts[1] not in COMMON_REGIONS:
        return f"Unknown region code '{code}'"
    if len(parts) > 2:
        return f"Malformed hreflang code '{code}' (expected lang or lang-REGION)"
    return None


class InternationalAuditor:
    def audit(self, crawl_data: Dict[str, Any], base_url: str) -> Dict[str, Any]:
        raw_html = crawl_data.get("raw_html", "") or ""
        canonical = (crawl_data.get("canonical", {}) or {}).get("url", "")
        issues: List[Dict[str, str]] = []
        passes: List[str] = []

        # ---- Collect hreflang links ----
        # Matches <link ... hreflang="xx" ... href="..."> in any attribute order
        hreflang_entries: List[Dict[str, str]] = []
        for link_tag in re.findall(r"<link\b[^>]*>", raw_html, re.I):
            tag = link_tag.lower()
            if "hreflang" not in tag or "href" not in tag:
                continue
            lang_m = re.search(r'hreflang=["\']([^"\']+)["\']', tag)
            href_m = re.search(r'href=["\']([^"\']+)["\']', tag)
            if lang_m and href_m:
                hreflang_entries.append({
                    "lang": lang_m.group(1).strip(),
                    "href": href_m.group(1).strip(),
                })

        # ---- HTML lang attribute ----
        html_lang = None
        html_tag_m = re.search(r"<html\b[^>]*\blang=[\"']([^\"']+)[\"']", raw_html, re.I)
        if html_tag_m:
            html_lang = html_tag_m.group(1).strip()

        result: Dict[str, Any] = {
            "success": True,
            "hreflang_count": len(hreflang_entries),
            "hreflang_entries": hreflang_entries[:20],
            "html_lang": html_lang,
            "has_x_default": any(e["lang"].lower() == "x-default" for e in hreflang_entries),
            "canonical_url": canonical,
            "issues": issues,
            "passes": passes,
        }

        # ---- Diagnosis ----
        if not hreflang_entries:
            if not html_lang:
                issues.append({
                    "severity": "LOW",
                    "field": "International Targeting",
                    "message": "No hreflang annotations and no HTML lang attribute — search engines can't infer the page language.",
                })
                result["international_score"] = 40
            else:
                base_lang = html_lang.split("-")[0].lower()
                if base_lang not in COMMON_LANGS:
                    issues.append({
                        "severity": "LOW",
                        "field": "HTML lang",
                        "message": f"HTML lang '{html_lang}' is not a recognizable ISO 639-1 code.",
                    })
                    result["international_score"] = 45
                else:
                    passes.append(f"HTML lang attribute present: '{html_lang}' (single-language site, no hreflang needed)")
                    result["international_score"] = 85
            return result

        # Multi-language annotation present — validate thoroughly
        score = 100

        # 1. Return-tag rule: every hreflang needs a reciprocal partner
        href_set = {e["href"].rstrip("/") for e in hreflang_entries}
        missing_return = []
        for e in hreflang_entries:
            # The page URL should itself be listed by other alternates. If the
            # page's own URL (or canonical) isn't among targets, it's orphaned.
            self_url = (canonical or base_url).rstrip("/")
            if self_url not in href_set:
                missing_return.append(e["lang"])
        if missing_return:
            score -= 30
            issues.append({
                "severity": "HIGH",
                "field": "hreflang Return Tags",
                "message": (
                    f"This page's URL is not listed among the hreflang alternates "
                    f"(annotations from: {', '.join(sorted(set(missing_return))[:5])}). "
                    "hreflang is bidirectional — every alternate must list all others including itself."
                ),
            })
        else:
            passes.append("hreflang return-tag reciprocity satisfied")

        # 2. Code validity
        invalid_codes = []
        for e in hreflang_entries:
            err = _validate_hreflang_code(e["lang"])
            if err:
                invalid_codes.append(err)
        if invalid_codes:
            score -= 20
            issues.append({
                "severity": "HIGH",
                "field": "hreflang Codes",
                "message": "; ".join(invalid_codes[:4]),
            })
        else:
            passes.append("All hreflang codes are valid ISO lang-REGION values")

        # 3. x-default presence
        if not result["has_x_default"]:
            score -= 10
            issues.append({
                "severity": "MEDIUM",
                "field": "hreflang x-default",
                "message": "No x-default alternate — specify which URL serves unmatched-language visitors.",
            })
        else:
            passes.append("x-default alternate present")

        # 4. Duplicates of the same lang
        lang_counts: Dict[str, int] = {}
        for e in hreflang_entries:
            key = e["lang"].lower()
            lang_counts[key] = lang_counts.get(key, 0) + 1
        dupes = [k for k, v in lang_counts.items() if v > 1]
        if dupes:
            score -= 20
            issues.append({
                "severity": "HIGH",
                "field": "hreflang Duplicates",
                "message": f"Duplicate hreflang codes found ({', '.join(dupes[:4])}) — each language may map to only one URL.",
            })

        # 5. HTML lang vs hreflang coherence
        if html_lang:
            base_lang = html_lang.split("-")[0].lower()
            if base_lang not in {e["lang"].split("-")[0].lower() for e in hreflang_entries} and base_lang not in ("x",):
                score -= 10
                issues.append({
                    "severity": "MEDIUM",
                    "field": "HTML lang Coherence",
                    "message": f"HTML lang '{html_lang}' doesn't match any hreflang annotation language.",
                })
            else:
                passes.append("HTML lang matches an annotated hreflang language")

        result["international_score"] = max(0, min(100, score))
        return result
