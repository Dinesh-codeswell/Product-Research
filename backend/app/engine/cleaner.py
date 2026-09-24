"""Text Normalizer, Noise Stripper, and Deduplication Engine"""
import hashlib
import re
from typing import List, Tuple
from app.channels.base import ChannelItem

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

    def deduplicate_and_clean(self, items: List[ChannelItem]) -> List[ChannelItem]:
        cleaned_items: List[ChannelItem] = []
        self._seen_hashes.clear()

        for item in items:
            cleaned_content = self.clean_text(item.content)
            
            # Skip low-signal items (< 40 characters)
            if len(cleaned_content) < 40:
                continue

            content_hash = self.compute_hash(cleaned_content)
            if content_hash in self._seen_hashes:
                continue

            self._seen_hashes.add(content_hash)
            item.content = cleaned_content
            cleaned_items.append(item)

        return cleaned_items
