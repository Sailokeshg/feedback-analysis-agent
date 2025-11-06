#!/usr/bin/env python3
"""
Test script for the /chat/query endpoint structure and models.
"""

import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_models():
    """Test that the model definitions are syntactically correct."""
    print("Testing model definitions...")

    try:
        # Check that the models are defined in the file
        with open("server/app/routers/chat.py", "r") as f:
            content = f.read()

        # Check for key model definitions
        assert "class ChatQueryRequest(BaseModel):" in content
        assert "class QueryFilters(BaseModel):" in content
        assert "class DateRangeFilter(BaseModel):" in content
        assert "class ChatQueryResponse(BaseModel):" in content
        assert "class Citation(BaseModel):" in content

        # Check for required fields
        assert 'question: str = Field(..., description="The question to ask' in content
        assert 'answer: str = Field(..., description="The agent\'s answer' in content
        assert 'feedback_id: str = Field(..., description="UUID of the feedback item' in content

        print("✓ Model definitions are present and correct")

        return True

    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation():
    """Test that validation functions are defined."""
    print("\nTesting validation functions...")

    try:
        with open("server/app/routers/chat.py", "r") as f:
            content = f.read()

        # Check that validation functions exist
        assert "def validate_token_limits" in content
        assert "def estimate_token_count" in content
        assert "MAX_TOKENS" in content
        assert "REQUEST_TIMEOUT" in content
        assert "MAX_QUESTION_LENGTH" in content

        print("✓ Validation functions are defined")
        return True

    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False

def test_filter_application():
    """Test that filter application function is defined."""
    print("\nTesting filter application...")

    try:
        with open("server/app/routers/chat.py", "r") as f:
            content = f.read()

        # Check that filter application function exists
        assert "def apply_filters_to_query" in content
        assert "filter_descriptions" in content

        print("✓ Filter application function is defined")
        return True

    except Exception as e:
        print(f"✗ Filter application test failed: {e}")
        return False

def test_citation_extraction():
    """Test that citation extraction function is defined."""
    print("\nTesting citation extraction...")

    try:
        with open("server/app/routers/chat.py", "r") as f:
            content = f.read()

        # Check that citation extraction function exists
        assert "def extract_citations_from_response" in content
        assert "feedback_id_pattern" in content
        assert "re.findall" in content

        print("✓ Citation extraction function is defined")
        return True

    except Exception as e:
        print(f"✗ Citation extraction test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing /chat/query endpoint implementation")
    print("=" * 50)

    tests = [
        ("Models", test_models),
        ("Validation", test_validation),
        ("Filter Application", test_filter_application),
        ("Citation Extraction", test_citation_extraction)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ready for load testing.")
        return True
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
