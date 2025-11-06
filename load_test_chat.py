#!/usr/bin/env python3
"""
Load testing script for the /chat/query endpoint.
Tests 5 concurrent requests on a dev machine.
"""

import asyncio
import aiohttp
import json
import time
import statistics
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8000"  # Adjust if different
CHAT_QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/query"
CONCURRENT_REQUESTS = 5
TEST_QUESTIONS = [
    "What are the main topics in customer feedback?",
    "Show me examples of negative feedback about product quality",
    "How has sentiment changed over time?",
    "What are the most common customer complaints?",
    "Generate a summary of recent feedback trends"
]

TEST_PAYLOADS = [
    {
        "question": question,
        "filters": {
            "date_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "sentiment": None,
            "topic_ids": None,
            "source": None,
            "customer_id": None,
            "language": None
        }
    }
    for question in TEST_QUESTIONS
]

async def make_request(session: aiohttp.ClientSession, payload: Dict[str, Any], request_id: int) -> Dict[str, Any]:
    """Make a single request and measure performance."""
    start_time = time.time()

    try:
        async with session.post(
            CHAT_QUERY_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
        ) as response:
            end_time = time.time()
            response_time = end_time - start_time

            if response.status == 200:
                result = await response.json()
                return {
                    "request_id": request_id,
                    "success": True,
                    "status_code": response.status,
                    "response_time": response_time,
                    "answer_length": len(result.get("answer", "")),
                    "citations_count": len(result.get("citations", [])),
                    "error": None
                }
            else:
                error_text = await response.text()
                return {
                    "request_id": request_id,
                    "success": False,
                    "status_code": response.status,
                    "response_time": response_time,
                    "answer_length": 0,
                    "citations_count": 0,
                    "error": error_text
                }

    except asyncio.TimeoutError:
        end_time = time.time()
        return {
            "request_id": request_id,
            "success": False,
            "status_code": None,
            "response_time": end_time - start_time,
            "answer_length": 0,
            "citations_count": 0,
            "error": "Request timed out"
        }
    except Exception as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "success": False,
            "status_code": None,
            "response_time": end_time - start_time,
            "answer_length": 0,
            "citations_count": 0,
            "error": str(e)
        }

async def run_load_test() -> Dict[str, Any]:
    """Run the load test with concurrent requests."""
    logger.info(f"Starting load test with {CONCURRENT_REQUESTS} concurrent requests")
    logger.info(f"API Endpoint: {CHAT_QUERY_ENDPOINT}")

    # Prepare test data - cycle through questions for the number of concurrent requests
    test_payloads = []
    for i in range(CONCURRENT_REQUESTS):
        payload = TEST_PAYLOADS[i % len(TEST_PAYLOADS)].copy()
        payload["question"] = f"{payload['question']} (Request {i+1})"
        test_payloads.append(payload)

    results = []
    total_start_time = time.time()

    async with aiohttp.ClientSession() as session:
        # Create concurrent tasks
        tasks = [
            make_request(session, payload, i+1)
            for i, payload in enumerate(test_payloads)
        ]

        # Execute all requests concurrently
        logger.info(f"Executing {len(tasks)} concurrent requests...")
        batch_start_time = time.time()

        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_end_time = time.time()
        total_batch_time = batch_end_time - batch_start_time

        # Process results
        for result in completed_results:
            if isinstance(result, Exception):
                logger.error(f"Request failed with exception: {result}")
                results.append({
                    "request_id": "unknown",
                    "success": False,
                    "status_code": None,
                    "response_time": 0,
                    "answer_length": 0,
                    "citations_count": 0,
                    "error": str(result)
                })
            else:
                results.append(result)

    total_end_time = time.time()
    total_test_time = total_end_time - total_start_time

    # Analyze results
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]

    response_times = [r["response_time"] for r in results if r["response_time"] > 0]

    analysis = {
        "total_requests": len(results),
        "successful_requests": len(successful_requests),
        "failed_requests": len(failed_requests),
        "success_rate": len(successful_requests) / len(results) if results else 0,
        "total_test_time": total_test_time,
        "batch_time": total_batch_time,
        "average_response_time": statistics.mean(response_times) if response_times else 0,
        "min_response_time": min(response_times) if response_times else 0,
        "max_response_time": max(response_times) if response_times else 0,
        "median_response_time": statistics.median(response_times) if response_times else 0,
        "requests_per_second": len(results) / total_batch_time if total_batch_time > 0 else 0,
        "results": results
    }

    return analysis

def print_results(analysis: Dict[str, Any]):
    """Print formatted test results."""
    print("\n" + "="*80)
    print("LOAD TEST RESULTS")
    print("="*80)

    print(f"Total Requests: {analysis['total_requests']}")
    print(f"Successful: {analysis['successful_requests']}")
    print(f"Failed: {analysis['failed_requests']}")
    print(".1f")
    print(f"Total Test Time: {analysis['total_test_time']:.2f}s")
    print(f"Batch Time: {analysis['batch_time']:.2f}s")
    print(f"Requests/Second: {analysis['requests_per_second']:.2f}")

    if analysis['average_response_time'] > 0:
        print("
Response Times:"        print(".2f"        print(".2f"        print(".2f"        print(".2f"
    print("\nIndividual Results:")
    for result in analysis['results']:
        status = "✓" if result['success'] else "✗"
        status_code = result['status_code'] or "ERR"
        print("2d"
              "6.2f"
              f"{result['citations_count']} citations"
    if analysis['failed_requests'] > 0:
        print("
Failed Requests:"        for result in analysis['results']:
            if not result['success']:
                print(f"  Request {result['request_id']}: {result['error']}")

    # Performance assessment
    print("
Performance Assessment:"    if analysis['success_rate'] >= 0.8 and analysis['average_response_time'] < 30:
        print("  ✅ EXCELLENT: High success rate and fast responses")
    elif analysis['success_rate'] >= 0.6 and analysis['average_response_time'] < 45:
        print("  ✅ GOOD: Acceptable performance for concurrent requests")
    elif analysis['success_rate'] >= 0.4:
        print("  ⚠️  FAIR: Some issues but mostly functional")
    else:
        print("  ❌ POOR: Significant performance issues")

async def main():
    """Main test function."""
    print("Feedback Analysis Chat Query Load Test")
    print(f"Testing {CONCURRENT_REQUESTS} concurrent requests")

    try:
        # Test basic connectivity first
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/healthz") as response:
                if response.status != 200:
                    print(f"❌ Server not healthy. Status: {response.status}")
                    return

        print("✅ Server is healthy, starting load test...")

        # Run the load test
        analysis = await run_load_test()
        print_results(analysis)

    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to server. Is it running?")
        print(f"   Make sure the server is running at {API_BASE_URL}")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
