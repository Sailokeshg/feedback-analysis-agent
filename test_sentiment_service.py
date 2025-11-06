#!/usr/bin/env python3
"""
Demo script for sentiment service - test both strategies and deterministic outputs.
"""

import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.sentiment_service import SentimentService


def test_vader_strategy():
    """Test VADER sentiment strategy."""
    print("=" * 60)
    print("Testing VADER Strategy")
    print("=" * 60)

    # Set environment variables
    os.environ["SENTIMENT_STRATEGY"] = "vader"
    os.environ["SENTIMENT_SEED"] = "42"

    service = SentimentService()

    # Test data with expected results
    test_texts = [
        "I love this product! It's amazing!",
        "This is absolutely terrible!",
        "It's okay, nothing special.",
        "Great customer service!",
        "Worst experience ever!",
        "",
    ]

    print("\nAnalyzing test texts:")
    print("-" * 40)

    results = []
    for text in test_texts:
        sentiment, score = service.analyze_sentiment(text)
        label = service.get_sentiment_label(sentiment)
        results.append((sentiment, score))

        if text:
            print("35")
        else:
            print("35")

    return results


def test_roberta_strategy():
    """Test RoBERTa sentiment strategy."""
    print("\n" + "=" * 60)
    print("Testing DistilRoBERTa Strategy")
    print("=" * 60)

    # Set environment variables
    os.environ["SENTIMENT_STRATEGY"] = "distilroberta"
    os.environ["SENTIMENT_SEED"] = "42"

    try:
        service = SentimentService()

        # Test data
        test_texts = [
            "I love this product! It's amazing!",
            "This is absolutely terrible!",
            "It's okay, nothing special.",
        ]

        print("\nAnalyzing test texts:")
        print("-" * 40)

        results = []
        for text in test_texts:
            sentiment, score = service.analyze_sentiment(text)
            label = service.get_sentiment_label(sentiment)
            results.append((sentiment, score))
            print("35")

        return results

    except Exception as e:
        print(f"❌ RoBERTa strategy failed: {e}")
        print("This is expected if transformers/torch are not installed.")
        return None


def test_deterministic_outputs():
    """Test that outputs are deterministic with the same seed."""
    print("\n" + "=" * 60)
    print("Testing Deterministic Outputs")
    print("=" * 60)

    test_texts = [
        "I love this!",
        "This is terrible!",
        "It's okay.",
        "Amazing product!",
        "Awful service!",
    ]

    # Test with VADER
    os.environ["SENTIMENT_STRATEGY"] = "vader"
    os.environ["SENTIMENT_SEED"] = "123"

    service1 = SentimentService()
    service2 = SentimentService()

    print("\nTesting VADER determinism:")
    print("-" * 30)

    all_match = True
    for text in test_texts:
        result1 = service1.analyze_sentiment(text)
        result2 = service2.analyze_sentiment(text)

        match = result1 == result2
        all_match = all_match and match

        status = "✅" if match else "❌"
        print("40")

    if all_match:
        print("\n✅ All VADER results are deterministic!")
    else:
        print("\n❌ VADER results are not deterministic!")

    return all_match


def test_accuracy_sanity():
    """Test accuracy on a tiny labeled dataset."""
    print("\n" + "=" * 60)
    print("Accuracy Sanity Check")
    print("=" * 60)

    # Tiny labeled dataset
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

    os.environ["SENTIMENT_STRATEGY"] = "vader"
    os.environ["SENTIMENT_SEED"] = "42"

    service = SentimentService()

    print("\nTesting accuracy on labeled dataset:")
    print("-" * 50)

    correct_predictions = 0
    total_predictions = len(test_data)

    for text, expected_sentiment in test_data:
        predicted_sentiment, confidence = service.analyze_sentiment(text)
        is_correct = predicted_sentiment == expected_sentiment

        if is_correct:
            correct_predictions += 1

        status = "✅" if is_correct else "❌"
        expected_label = service.get_sentiment_label(expected_sentiment)
        predicted_label = service.get_sentiment_label(predicted_sentiment)

        print("50")

    accuracy = correct_predictions / total_predictions
    print("\n📊 Results:")
    print(".1%")
    print(f"   Total samples: {total_predictions}")

    if accuracy >= 0.7:
        print("✅ Accuracy looks reasonable!")
    else:
        print("⚠️  Accuracy is lower than expected - this may indicate issues.")

    return accuracy


def main():
    """Run all sentiment service tests."""
    print("🤖 Sentiment Service Demo")
    print("Testing VADER and DistilRoBERTa sentiment analysis strategies")

    try:
        # Test VADER
        vader_results = test_vader_strategy()

        # Test RoBERTa (may fail if dependencies not installed)
        roberta_results = test_roberta_strategy()

        # Test determinism
        deterministic = test_deterministic_outputs()

        # Test accuracy
        accuracy = test_accuracy_sanity()

        # Summary
        print("\n" + "=" * 60)
        print("📋 SUMMARY")
        print("=" * 60)

        print("✅ VADER Strategy: Working")
        if roberta_results is not None:
            print("✅ DistilRoBERTa Strategy: Working")
        else:
            print("⚠️  DistilRoBERTa Strategy: Not available (missing dependencies)")

        if deterministic:
            print("✅ Deterministic Outputs: Confirmed")
        else:
            print("❌ Deterministic Outputs: Failed")

        print(".1%")

        print("\n💡 Configuration:")
        print("   SENTIMENT_STRATEGY: vader (default) | distilroberta")
        print("   SENTIMENT_SEED: 42 (default) | any integer")

        print("\n🔧 Usage:")
        print("   export SENTIMENT_STRATEGY=vader  # or distilroberta")
        print("   export SENTIMENT_SEED=42         # for reproducible results")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
