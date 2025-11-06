"""
Text processing service for normalization and language detection.
"""

import re
import logging
from typing import Optional, Tuple
import os

logger = logging.getLogger(__name__)

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    logger.warning("fasttext not available, language detection disabled")


class TextProcessingService:
    """Service for text normalization and language detection."""

    def __init__(self):
        self.language_detector = None
        self._initialize_language_detector()

    def _initialize_language_detector(self):
        """Initialize fasttext language detection model."""
        if not FASTTEXT_AVAILABLE:
            logger.info("Fasttext not available, skipping language detector initialization")
            return

        try:
            # Try to load the fasttext language detection model
            # This will be a small model for language identification
            model_path = os.getenv("FASTTEXT_MODEL_PATH", "lid.176.bin")

            # Check if model exists, if not we'll handle it gracefully
            if os.path.exists(model_path):
                self.language_detector = fasttext.load_model(model_path)
                logger.info("Fasttext language detection model loaded successfully")
            else:
                logger.warning(f"Fasttext model not found at {model_path}, language detection disabled")
                self.language_detector = None

        except Exception as e:
            logger.error(f"Failed to load fasttext model: {e}")
            self.language_detector = None

    def normalize_text(self, text: str) -> str:
        """
        Normalize text by applying various cleaning operations.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        if not text or not isinstance(text, str):
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Remove URLs
        normalized = self._remove_urls(normalized)

        # Remove email addresses
        normalized = self._remove_emails(normalized)

        # Remove user mentions (@username)
        normalized = self._remove_mentions(normalized)

        # Remove extra whitespace
        normalized = self._clean_whitespace(normalized)

        return normalized.strip()

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text.

        Args:
            text: Input text to analyze

        Returns:
            ISO 639-1 language code or None if detection fails/unavailable
        """
        if not self.language_detector or not text or not isinstance(text, str):
            return None

        try:
            # Fasttext returns predictions as tuples of (label, confidence)
            predictions = self.language_detector.predict(text, k=1)

            if predictions and len(predictions[0]) > 0:
                # Label format is '__label__<lang_code>'
                label = predictions[0][0]
                confidence = predictions[1][0]

                # Only return language if confidence is above threshold
                if confidence > 0.5:  # 50% confidence threshold
                    lang_code = label.replace('__label__', '')
                    return lang_code

        except Exception as e:
            logger.error(f"Language detection failed: {e}")

        return None

    def process_text(self, text: str, skip_non_english: bool = True) -> Tuple[str, Optional[str], bool]:
        """
        Process text with normalization and optional language filtering.

        Args:
            text: Input text to process
            skip_non_english: Whether to skip non-English text

        Returns:
            Tuple of (normalized_text, detected_language, should_process)
            should_process indicates whether the text should be processed further
        """
        normalized = self.normalize_text(text)

        if not normalized:
            return normalized, None, False

        detected_lang = self.detect_language(normalized)

        # If language detection is enabled and we should skip non-English
        if skip_non_english and detected_lang and detected_lang != 'en':
            logger.info(f"Skipping non-English text (detected: {detected_lang})")
            return normalized, detected_lang, False

        return normalized, detected_lang, True

    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        # Match various URL patterns
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))*)?'
        return re.sub(url_pattern, '', text, flags=re.IGNORECASE)

    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)

    def _remove_mentions(self, text: str) -> str:
        """Remove user mentions (@username) from text."""
        mention_pattern = r'@\w+'
        return re.sub(mention_pattern, '', text)

    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
