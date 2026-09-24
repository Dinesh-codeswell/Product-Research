"""Keyword Extraction, Intent Analysis & Content Completeness Scorer"""
import re
from collections import Counter
from typing import Dict, Any, List

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

class KeywordAndContentAnalyzer:
    def analyze(self, visible_text: str, headings: Dict[str, Any], raw_html: str) -> Dict[str, Any]:
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", visible_text)]
        word_count = len(words)

        # 1. Candidate Keyword Extraction (Unigrams & Bigrams)
        meaningful_words = [w for w in words if w not in STOP_WORDS]
        unigram_counts = Counter(meaningful_words)

        bigrams = []
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            if w1 not in STOP_WORDS and w2 not in STOP_WORDS:
                bigrams.append(f"{w1} {w2}")
        bigram_counts = Counter(bigrams)

        # Classify Search Intent
        keywords_data = []
        h1_text = " ".join(headings.get("h1", [])).lower()
        h2_text = " ".join(headings.get("h2", [])).lower()

        # Top bigrams first, then top unigrams
        top_candidates = bigram_counts.most_common(12) + unigram_counts.most_common(12)
        seen = set()

        for term, count in top_candidates:
            if term in seen or len(term) < 4:
                continue
            seen.add(term)

            # Intent heuristic
            term_lower = term.lower()
            if any(k in term_lower for k in ["how", "what", "guide", "overview", "explained", "learn", "architecture"]):
                intent = "Informational"
            elif any(k in term_lower for k in ["best", "review", "vs", "alternative", "comparison", "pricing", "top"]):
                intent = "Commercial"
            elif any(k in term_lower for k in ["buy", "download", "login", "signup", "deploy", "hire", "install", "api"]):
                intent = "Transactional"
            else:
                intent = "Navigational / Brand"

            in_h1 = term_lower in h1_text
            in_h2 = term_lower in h2_text
            density = round((count / max(1, word_count)) * 100, 2)

            keywords_data.append({
                "keyword": term,
                "frequency": count,
                "density_percent": density,
                "intent": intent,
                "in_h1": in_h1,
                "in_h2": in_h2,
                "prominence": "HIGH" if (in_h1 or in_h2) else "NORMAL"
            })

        # 2. Content Completeness Score (0-100)
        # Dimensions:
        # Depth: max 25
        if word_count >= 800:
            depth_score = 25
        elif word_count >= 400:
            depth_score = 18
        elif word_count >= 200:
            depth_score = 10
        else:
            depth_score = 4

        # Structure: max 25
        h1_c = headings.get("h1_count", 0)
        h2_c = headings.get("h2_count", 0)
        h3_c = headings.get("h3_count", 0)
        structure_score = min(25, (10 if h1_c == 1 else 4) + min(10, h2_c * 3) + min(5, h3_c * 1))

        # Evidence: max 20
        numbers_found = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", visible_text))
        evidence_score = min(20, numbers_found * 2)

        # Elements: max 15 (lists, code, tables)
        has_lists = "<ul" in raw_html or "<ol" in raw_html
        has_code = "<code" in raw_html or "<pre" in raw_html
        has_tables = "<table" in raw_html
        elements_score = (7 if has_lists else 0) + (5 if has_code else 0) + (3 if has_tables else 0)

        # Entity Breadth: max 15
        entity_score = min(15, len(unigram_counts) // 5)

        total_completeness = min(100, depth_score + structure_score + evidence_score + elements_score + entity_score)

        return {
            "content_completeness_score": total_completeness,
            "word_count": word_count,
            "dimensions": {
                "depth": {"score": depth_score, "max": 25},
                "structure": {"score": structure_score, "max": 25},
                "evidence_and_stats": {"score": evidence_score, "max": 20},
                "rich_elements": {"score": elements_score, "max": 15},
                "topical_breadth": {"score": entity_score, "max": 15}
            },
            "top_keywords": keywords_data[:15],
            "thin_content_warning": word_count < 250
        }
