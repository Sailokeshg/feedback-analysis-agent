from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import os

class SentimentService:
    def __init__(self):
        # Use VADER for fast sentiment analysis
        self.vader_analyzer = SentimentIntensityAnalyzer()

        # Optional: Use Hugging Face model for more accurate analysis
        use_hf = os.getenv("USE_HF_SENTIMENT", "false").lower() == "true"
        if use_hf:
            self.hf_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        else:
            self.hf_analyzer = None

    def analyze_sentiment(self, text: str) -> tuple[str, float]:
        """Analyze sentiment of text and return (sentiment, score)"""
        if self.hf_analyzer:
            # Use Hugging Face model
            result = self.hf_analyzer(text)[0]
            label = result['label'].lower()
            score = result['score']

            # Map labels to our format
            if label == 'label_2':  # positive
                return 'positive', score
            elif label == 'label_0':  # negative
                return 'negative', score
            else:  # neutral
                return 'neutral', score
        else:
            # Use VADER
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores['compound']

            if compound >= 0.05:
                return 'positive', compound
            elif compound <= -0.05:
                return 'negative', compound
            else:
                return 'neutral', compound

    def analyze_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        """Analyze sentiment for a batch of texts"""
        return [self.analyze_sentiment(text) for text in texts]
