import os
import logging
from typing import Tuple, List, Optional
import random
import numpy as np

logger = logging.getLogger(__name__)

class SentimentService:
    """Sentiment analysis service with multiple strategies.

    Supports two strategies:
    1. VADER: Fast rule-based sentiment analysis
    2. DistilRoBERTa: Transformer-based sentiment analysis

    Choose strategy via SENTIMENT_STRATEGY env var:
    - "vader" (default): Fast rule-based analysis
    - "distilroberta": More accurate transformer model
    """

    def __init__(self):
        self.strategy = os.getenv("SENTIMENT_STRATEGY", "vader").lower()
        self.vader_analyzer = None
        self.roberta_analyzer = None

        # Set deterministic seed for reproducible results
        seed = int(os.getenv("SENTIMENT_SEED", "42"))
        random.seed(seed)
        np.random.seed(seed)

        logger.info(f"Initializing sentiment service with strategy: {self.strategy}")

        if self.strategy == "vader":
            self._initialize_vader()
        elif self.strategy == "distilroberta":
            self._initialize_roberta()
        else:
            logger.warning(f"Unknown sentiment strategy '{self.strategy}', falling back to VADER")
            self.strategy = "vader"
            self._initialize_vader()

    def _initialize_vader(self):
        """Initialize VADER sentiment analyzer."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized successfully")
        except ImportError:
            logger.error("VADER not available. Install with: pip install vaderSentiment")
            raise

    def _initialize_roberta(self):
        """Initialize DistilRoBERTa sentiment analyzer."""
        try:
            from transformers import pipeline, set_seed

            # Set seed for reproducible results
            seed = int(os.getenv("SENTIMENT_SEED", "42"))
            set_seed(seed)

            self.roberta_analyzer = pipeline(
                "sentiment-analysis",
                model="j-hartmann/emotion-english-distilroberta-base",
                device="cpu",  # Force CPU usage
                return_all_scores=True
            )
            logger.info("DistilRoBERTa sentiment analyzer initialized successfully")
        except ImportError:
            logger.error("Transformers not available. Install with: pip install transformers torch")
            raise

    def analyze_sentiment(self, text: str) -> Tuple[int, float]:
        """
        Analyze sentiment of text and return normalized results.

        Returns:
            Tuple of (sentiment, confidence_score)
            sentiment: -1 (negative), 0 (neutral), 1 (positive)
            confidence_score: float between 0 and 1
        """
        if not text or not text.strip():
            return 0, 0.0  # Neutral for empty text

        if self.strategy == "vader":
            return self._analyze_vader(text)
        elif self.strategy == "distilroberta":
            return self._analyze_roberta(text)
        else:
            logger.error(f"Unknown strategy: {self.strategy}")
            return 0, 0.0

    def _analyze_vader(self, text: str) -> Tuple[int, float]:
        """Analyze sentiment using VADER (rule-based)."""
        if not self.vader_analyzer:
            raise RuntimeError("VADER analyzer not initialized")

        scores = self.vader_analyzer.polarity_scores(text)
        compound = scores['compound']

        # Normalize to {-1, 0, 1}
        if compound >= 0.05:
            sentiment = 1  # positive
        elif compound <= -0.05:
            sentiment = -1  # negative
        else:
            sentiment = 0  # neutral

        # Use absolute compound score as confidence
        confidence = min(abs(compound), 1.0)

        return sentiment, confidence

    def _analyze_roberta(self, text: str) -> Tuple[int, float]:
        """Analyze sentiment using DistilRoBERTa (transformer-based)."""
        if not self.roberta_analyzer:
            raise RuntimeError("RoBERTa analyzer not initialized")

        # Get all scores for emotion analysis
        results = self.roberta_analyzer(text)[0]

        # Map emotions to sentiment
        # The model outputs: anger, disgust, fear, joy, neutral, sadness, surprise
        emotion_scores = {result['label']: result['score'] for result in results}

        # Calculate sentiment scores
        positive_score = emotion_scores.get('joy', 0.0)
        negative_score = (
            emotion_scores.get('anger', 0.0) +
            emotion_scores.get('disgust', 0.0) +
            emotion_scores.get('fear', 0.0) +
            emotion_scores.get('sadness', 0.0)
        ) / 4  # Average of negative emotions
        neutral_score = emotion_scores.get('neutral', 0.0)

        # Determine dominant sentiment
        scores = [negative_score, neutral_score, positive_score]
        max_score = max(scores)
        sentiment_idx = scores.index(max_score)

        # Map to {-1, 0, 1}
        sentiment = sentiment_idx - 1  # 0->-1, 1->0, 2->1

        return sentiment, max_score

    def analyze_batch(self, texts: List[str]) -> List[Tuple[int, float]]:
        """Analyze sentiment for a batch of texts."""
        return [self.analyze_sentiment(text) for text in texts]

    def get_sentiment_label(self, sentiment: int) -> str:
        """Convert numeric sentiment to human-readable label."""
        if sentiment == 1:
            return "positive"
        elif sentiment == -1:
            return "negative"
        else:
            return "neutral"
