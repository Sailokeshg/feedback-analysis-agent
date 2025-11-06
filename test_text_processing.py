#!/usr/bin/env python3
"""
Simple test script for text processing service.
"""

import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.text_processing_service import TextProcessingService

def test_text_processing():
    """Test text processing functionality."""
    service = TextProcessingService()

    # Test cases
    test_cases = [
        {
            "input": "HELLO @user! Check out https://example.com and email me at test@example.com",
            "expected_contains": ["hello", "check", "out"],
            "expected_not_contains": ["@user", "https://", "@example.com"]
        },
        {
            "input": "Simple text without special content.",
            "expected_contains": ["simple", "text"],
            "expected_not_contains": []
        },
        {
            "input": "",
            "expected_contains": [],
            "expected_not_contains": []
        }
    ]

    print("Testing Text Processing Service...")
    print("=" * 50)

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: '{case['input']}'")

        result = service.normalize_text(case['input'])
        print(f"Output: '{result}'")

        # Check expectations
        for expected in case['expected_contains']:
            if expected.lower() in result.lower():
                print(f"✓ Contains expected: '{expected}'")
            else:
                print(f"✗ Missing expected: '{expected}'")

        for not_expected in case['expected_not_contains']:
            if not_expected.lower() not in result.lower():
                print(f"✓ Correctly removed: '{not_expected}'")
            else:
                print(f"✗ Still contains: '{not_expected}'")

    # Test language detection (should be None without fasttext)
    print(f"\nLanguage detection test:")
    lang = service.detect_language("Hello world")
    print(f"Detected language: {lang}")

    # Test full processing
    print(f"\nFull processing test:")
    text = "HELLO WORLD @user!"
    normalized, detected_lang, should_process = service.process_text(text, skip_non_english=False)
    print(f"Input: '{text}'")
    print(f"Normalized: '{normalized}'")
    print(f"Language: {detected_lang}")
    print(f"Should process: {should_process}")

    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_text_processing()
