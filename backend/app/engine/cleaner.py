"""Text Normalizer, Noise Stripper, and Deduplication Engine"""
import hashlib
import re
from typing import List, Tuple
from app.channels.base import ChannelItem

from app.engine.laya_client import LayaEngine

class TextCleaner:
    # Regex patterns for stripping noise
    BOT_PATTERNS = [
        r"i am a bot, and this action was performed automatically",
        r"please contact the moderators of this subreddit",
        r"join our discord server",
        r"subscribe to my channel",
        r"click the link below"
    ]
    URL_PATTERN = r"https?://\S+|www\.\S+"

    def __init__(self):
        self._seen_hashes = set()
        self.laya = LayaEngine()

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Lowercase for noise check
        cleaned = text
        for pat in self.BOT_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def compute_hash(self, text: str) -> str:
        # Normalize and compute SHA-256
        norm = re.sub(r"[^a-zA-Z0-9]", "", text.lower())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def deduplicate_and_clean(self, items: List[ChannelItem], query: str = "") -> List[ChannelItem]:
        cleaned_items: List[ChannelItem] = []
        candidates: List[ChannelItem] = []
        self._seen_hashes.clear()

        for item in items:
            cleaned_content = self.clean_text(item.content)
            
            # Skip low-signal items (< 35 characters)
            if len(cleaned_content) < 35:
                continue

            content_hash = self.compute_hash(cleaned_content)
            if content_hash in self._seen_hashes:
                continue

            self._seen_hashes.add(content_hash)
            item.content = cleaned_content
            candidates.append(item)

            # Laya System 1 Semantic Relevance & Triage Gating
            if query:
                eval_meta = self.laya.evaluate_signal(cleaned_content, query)
                if not eval_meta.get("is_relevant", True):
                    continue

                item.raw_metadata = item.raw_metadata or {}
                item.raw_metadata["laya_category"] = eval_meta.get("category", "PAIN_POINT")
                item.raw_metadata["laya_severity"] = eval_meta.get("severity", 0.65)
                item.raw_metadata["laya_confidence"] = eval_meta.get("confidence", 0.70)
                item.sentiment_score = -0.6 if eval_meta.get("category") in ["PAIN_POINT", "CHURN_TRIGGER"] else 0.3

            cleaned_items.append(item)

        # Safety Fallback: If query gating filtered out all items but deduplicated candidates exist,
        # retain candidates with safe baseline metadata to prevent empty signal starvation downstream.
        if query and not cleaned_items and candidates:
            for item in candidates:
                item.raw_metadata = item.raw_metadata or {}
                item.raw_metadata["laya_category"] = "PAIN_POINT"
                item.raw_metadata["laya_severity"] = 0.50
                item.raw_metadata["laya_confidence"] = 0.50
                item.sentiment_score = -0.3
                cleaned_items.append(item)

        return cleaned_items

