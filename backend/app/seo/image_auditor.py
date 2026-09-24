"""Image SEO Auditor
Evaluates alt text coverage, modern formats (WebP/AVIF),
Cumulative Layout Shift (CLS) dimension attributes, and lazy loading.
"""
from typing import Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class ImageSeoAuditor:
    def audit(self, base_url: str, raw_html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(raw_html, "html.parser")
        img_tags = soup.find_all("img")

        total_images = len(img_tags)
        if total_images == 0:
            return {
                "score": 100,
                "total_images": 0,
                "missing_alt_count": 0,
                "alt_coverage_percent": 100,
                "modern_format_percent": 100,
                "cls_safe_percent": 100,
                "images": [],
                "issues": []
            }

        missing_alt = 0
        legacy_formats = 0
        missing_dimensions = 0
        lazy_loaded = 0
        analyzed_images = []
        issues = []

        for img in img_tags:
            src = img.get("src", "").strip() or img.get("data-src", "").strip()
            if not src:
                continue

            full_src = urljoin(base_url, src)
            alt = img.get("alt", None)
            has_alt = alt is not None and len(alt.strip()) > 0
            if not has_alt:
                missing_alt += 1

            # Format check
            ext = src.split("?")[0].lower().rsplit(".", 1)[-1] if "." in src.split("?")[0] else ""
            is_modern = ext in ("webp", "avif", "svg")
            if not is_modern and ext in ("jpg", "jpeg", "png", "gif"):
                legacy_formats += 1

            # Dimensions check (width & height attributes protect against CLS)
            has_dimensions = bool(img.get("width") and img.get("height"))
            if not has_dimensions:
                missing_dimensions += 1

            # Lazy loading
            is_lazy = img.get("loading") == "lazy"
            if is_lazy:
                lazy_loaded += 1

            analyzed_images.append({
                "src": full_src[:100],
                "alt": alt if alt is not None else "(missing)",
                "has_alt": has_alt,
                "format": ext.upper() if ext else "UNKNOWN",
                "is_modern": is_modern,
                "has_dimensions": has_dimensions,
                "is_lazy": is_lazy
            })

        alt_coverage = round(((total_images - missing_alt) / total_images) * 100)
        modern_coverage = round(((total_images - legacy_formats) / total_images) * 100)
        cls_safe_coverage = round(((total_images - missing_dimensions) / total_images) * 100)

        # Score calculation (0-100)
        score = 100
        if missing_alt > 0:
            deduction = min(35, round((missing_alt / total_images) * 40))
            score -= deduction
            issues.append({
                "severity": "HIGH",
                "category": "Accessibility & Alt Text",
                "message": f"{missing_alt} of {total_images} images lack descriptive 'alt' text."
            })
        if legacy_formats > 0:
            deduction = min(20, round((legacy_formats / total_images) * 20))
            score -= deduction
            issues.append({
                "severity": "MEDIUM",
                "category": "Image Format",
                "message": f"{legacy_formats} images use legacy formats (PNG/JPEG). Convert to WebP or AVIF to save bandwidth."
            })
        if missing_dimensions > 0:
            deduction = min(15, round((missing_dimensions / total_images) * 15))
            score -= deduction
            issues.append({
                "severity": "LOW",
                "category": "Core Web Vitals (CLS)",
                "message": f"{missing_dimensions} images lack explicit width/height attributes, risking layout shifts."
            })

        final_score = max(0, min(100, score))

        return {
            "score": final_score,
            "total_images": total_images,
            "missing_alt_count": missing_alt,
            "alt_coverage_percent": alt_coverage,
            "modern_format_percent": modern_coverage,
            "cls_safe_percent": cls_safe_coverage,
            "lazy_loaded_count": lazy_loaded,
            "images": analyzed_images[:25],
            "issues": issues
        }
