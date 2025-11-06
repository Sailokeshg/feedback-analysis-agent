"""
Unit tests for sentiment service - VADER and DistilRoBERTa strategies.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.sentiment_service import SentimentService


class TestSentimentService:
    """Test sentiment service functionality."""

    def test_vader_initialization(self):
        """Test VADER strategy initialization."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()
            assert service.strategy == "vader"
            assert service.vader_analyzer is not None
            assert service.roberta_analyzer is None

    def test_roberta_initialization(self):
        """Test RoBERTa strategy initialization."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "distilroberta"}):
            with patch('transformers.pipeline') as mock_pipeline:
                service = SentimentService()
                assert service.strategy == "distilroberta"
                assert service.roberta_analyzer is not None
                mock_pipeline.assert_called_once()

    def test_unknown_strategy_fallback(self):
        """Test unknown strategy falls back to VADER."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "unknown"}):
            service = SentimentService()
            assert service.strategy == "vader"
            assert service.vader_analyzer is not None

    def test_vader_sentiment_analysis(self):
        """Test VADER sentiment analysis with various inputs."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()

            test_cases = [
                # (text, expected_sentiment, expected_range)
                ("I love this product!", 1, (0.4, 1.0)),  # Positive
                ("This is terrible!", -1, (0.4, 1.0)),    # Negative
                ("It's okay.", 0, (0.0, 0.3)),           # Neutral
                ("", 0, (0.0, 0.0)),                     # Empty
                ("   ", 0, (0.0, 0.0)),                  # Whitespace
            ]

            for text, expected_sentiment, score_range in test_cases:
                sentiment, score = service.analyze_sentiment(text)
                assert sentiment == expected_sentiment, f"Failed for text: '{text}'"
                assert score_range[0] <= score <= score_range[1], f"Score {score} out of range for text: '{text}'"

    def test_roberta_sentiment_analysis(self):
        """Test RoBERTa sentiment analysis."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "distilroberta"}):
            # Mock the pipeline response
            mock_result = [
                {'label': 'joy', 'score': 0.8},
                {'label': 'neutral', 'score': 0.1},
                {'label': 'anger', 'score': 0.05},
                {'label': 'disgust', 'score': 0.02},
                {'label': 'fear', 'score': 0.02},
                {'label': 'sadness', 'score': 0.01},
            ]

            with patch('transformers.pipeline') as mock_pipeline_class:
                mock_pipeline = MagicMock()
                mock_pipeline.return_value = [mock_result]
                mock_pipeline_class.return_value = mock_pipeline

                service = SentimentService()
                sentiment, score = service.analyze_sentiment("I love this!")

                assert sentiment == 1  # Positive (joy)
                assert score == 0.8

    def test_deterministic_outputs_with_seed(self):
        """Test that outputs are deterministic with seed."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader", "SENTIMENT_SEED": "123"}):
            service1 = SentimentService()
            service2 = SentimentService()

            test_texts = [
                "This is amazing!",
                "I hate this product.",
                "It's just okay.",
                "Best purchase ever!",
                "Worst experience ever."
            ]

            results1 = [service1.analyze_sentiment(text) for text in test_texts]
            results2 = [service2.analyze_sentiment(text) for text in test_texts]

            assert results1 == results2, "Results should be identical with same seed"

    def test_batch_analysis(self):
        """Test batch sentiment analysis."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()

            texts = ["Great product!", "Terrible service!", "Okay experience."]
            results = service.analyze_batch(texts)

            assert len(results) == 3
            assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
            assert all(isinstance(r[0], int) and -1 <= r[0] <= 1 for r in results)
            assert all(isinstance(r[1], float) and 0 <= r[1] <= 1 for r in results)

    def test_sentiment_label_conversion(self):
        """Test sentiment label conversion."""
        service = SentimentService()

        assert service.get_sentiment_label(1) == "positive"
        assert service.get_sentiment_label(-1) == "negative"
        assert service.get_sentiment_label(0) == "neutral"

    def test_accuracy_sanity_check(self):
        """Accuracy sanity check on tiny labeled dataset."""
        # Tiny labeled dataset for sanity checking
        test_data = [
            ("I love this product! It's amazing!", 1),
            ("This is the best purchase I've made!", 1),
            ("Great quality and fast shipping!", 1),
            ("This product is terrible!", -1),
            ("Worst customer service ever!", -1),
            ("I hate this item!", -1),
            ("It's okay, nothing special.", 0),
            ("Average product, does the job.", 0),
            ("Neutral experience overall.", 0),
        ]

        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()

            correct_predictions = 0
            total_predictions = len(test_data)

            for text, expected_sentiment in test_data:
                predicted_sentiment, _ = service.analyze_sentiment(text)
                if predicted_sentiment == expected_sentiment:
                    correct_predictions += 1

            accuracy = correct_predictions / total_predictions
            print(".1%")

            # VADER should perform reasonably well on this simple dataset
            assert accuracy >= 0.7, f"VADER accuracy {accuracy:.1%} is too low"

    def test_roberta_accuracy_sanity_check(self):
        """Accuracy sanity check for RoBERTa on emotion dataset."""
        # For RoBERTa, we'll test emotion-based sentiment mapping
        test_data = [
            ("I'm so happy with this!", 1, "joy"),
            ("This makes me angry!", -1, "anger"),
            ("I'm really sad about this.", -1, "sadness"),
            ("This is disgusting.", -1, "disgust"),
            ("I'm scared to use this.", -1, "fear"),
            ("This is just normal.", 0, "neutral"),
        ]

        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "distilroberta"}):
            with patch('transformers.pipeline') as mock_pipeline_class:
                mock_pipeline = MagicMock()
                mock_pipeline_class.return_value = mock_pipeline

                service = SentimentService()

                for text, expected_sentiment, expected_emotion in test_data:
                    # Mock the pipeline to return high score for expected emotion
                    mock_result = [
                        {'label': expected_emotion, 'score': 0.9},
                        {'label': 'neutral', 'score': 0.05},
                        {'label': 'joy', 'score': 0.02},
                        {'label': 'anger', 'score': 0.01},
                        {'label': 'disgust', 'score': 0.01},
                        {'label': 'fear', 'score': 0.01},
                        {'label': 'sadness', 'score': 0.0},
                    ]
                    mock_pipeline.return_value = [mock_result]

                    sentiment, score = service.analyze_sentiment(text)
                    assert sentiment == expected_sentiment, f"Failed for text: '{text}'"
                    assert score >= 0.8, f"Low confidence for text: '{text}'"

    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()

            # Test with None analyzer (simulate initialization failure)
            service.vader_analyzer = None

            with pytest.raises(RuntimeError):
                service.analyze_sentiment("test text")

    def test_roberta_error_handling(self):
        """Test RoBERTa error handling."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "distilroberta"}):
            with patch('transformers.pipeline') as mock_pipeline_class:
                mock_pipeline = MagicMock()
                mock_pipeline.side_effect = Exception("Pipeline error")
                mock_pipeline_class.return_value = mock_pipeline

                service = SentimentService()
                service.roberta_analyzer = mock_pipeline

                # Should handle gracefully and return neutral
                sentiment, score = service.analyze_sentiment("test text")
                assert sentiment == 0
                assert score == 0.0

    def test_empty_and_whitespace_text(self):
        """Test handling of empty and whitespace-only text."""
        service = SentimentService()

        test_cases = ["", "   ", "\t\n  ", None]

        for text in test_cases:
            sentiment, score = service.analyze_sentiment(text)
            assert sentiment == 0  # Neutral
            assert score == 0.0

    def test_vader_score_ranges(self):
        """Test that VADER scores are properly clamped and in expected ranges."""
        with patch.dict(os.environ, {"SENTIMENT_STRATEGY": "vader"}):
            service = SentimentService()

            # Test various sentiment strengths
            texts = [
                "This is absolutely fantastic!!!",
                "I really like this.",
                "It's decent.",
                "Not great.",
                "This is awful.",
                "HORRIBLE EXPERIENCE!!!"
            ]

            for text in texts:
                sentiment, score = service.analyze_sentiment(text)
                assert -1 <= sentiment <= 1
                assert 0 <= score <= 1

                # Stronger language should generally have higher confidence
                # (This is a soft test - not guaranteed but expected)
