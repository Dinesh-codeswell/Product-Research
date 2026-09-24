"""Vector Embedding Generator with Local & Fast Scikit-Learn Pipeline"""
import logging
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=512,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0))
        
        try:
            matrix = self.vectorizer.fit_transform(texts)
            return matrix.toarray()
        except Exception as e:
            logger.error(f"Error vectorizing texts: {e}")
            # Fallback zero-array
            return np.zeros((len(texts), 64))
