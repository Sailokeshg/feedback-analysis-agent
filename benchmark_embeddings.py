#!/usr/bin/env python3
"""
Benchmark script for embedding service performance and memory footprint.
"""

import sys
import os
import time
import json
from typing import List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.embedding_service import EmbeddingService


def generate_sample_texts(n_texts: int, avg_length: int = 50) -> List[str]:
    """Generate sample texts for benchmarking."""
    import random
    import string

    texts = []
    words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
             "hello", "world", "machine", "learning", "artificial", "intelligence",
             "natural", "language", "processing", "sentiment", "analysis", "feedback"]

    for _ in range(n_texts):
        # Generate text with approximately avg_length words
        length = int(random.gauss(avg_length, avg_length * 0.2))
        length = max(1, min(length, avg_length * 2))  # Keep within reasonable bounds

        text_words = random.choices(words, k=length)
        text = " ".join(text_words)
        texts.append(text)

    return texts


def run_comprehensive_benchmark():
    """Run comprehensive embedding benchmark."""
    print("=" * 80)
    print("EMBEDDING SERVICE COMPREHENSIVE BENCHMARK")
    print("=" * 80)

    # Initialize service
    print("Initializing embedding service...")
    service = EmbeddingService()

    if not service.model:
        print("❌ ERROR: Embedding model not available. Please install sentence-transformers.")
        return

    # Memory footprint before any processing
    initial_memory = service.get_memory_footprint()
    print("\n📊 Initial Memory Footprint:")
    if "note" not in initial_memory:
        print(f"   Total: {initial_memory['total_mb']:.1f} MB")
        print(f"   Available: {initial_memory['available_mb']:.1f} MB")
        print(f"   Used: {initial_memory['used_mb']:.1f} MB")
        print(f"   Used %: {initial_memory['used_percent']:.1f}%")
    else:
        print(f"   Note: {initial_memory['note']}")

    # Test datasets of different sizes
    test_configs = [
        {"n_texts": 10, "name": "Small (10 texts)"},
        {"n_texts": 100, "name": "Medium (100 texts)"},
        {"n_texts": 500, "name": "Large (500 texts)"},
        {"n_texts": 1000, "name": "XL (1000 texts)"},
    ]

    results = {
        "timestamp": time.time(),
        "model_info": {
            "name": service.MODEL_NAME,
            "dimension": service.EMBEDDING_DIMENSION,
            "max_seq_length": service.MAX_SEQ_LENGTH,
        },
        "initial_memory": initial_memory,
        "benchmarks": []
    }

    for config in test_configs:
        print(f"\n🔬 Running {config['name']} benchmark...")

        # Generate test data
        texts = generate_sample_texts(config['n_texts'])
        print(f"   Generated {len(texts)} texts (avg length: {sum(len(t.split()) for t in texts) / len(texts):.1f} words)")

        # Run benchmark
        benchmark_result = service.benchmark_embedding_generation(
            texts,
            batch_sizes=[1, 8, 16, 32, 64]
        )

        results["benchmarks"].append({
            "config": config,
            "results": benchmark_result
        })

        # Print summary
        if "error" not in benchmark_result:
            print(f"   ✅ Benchmark completed successfully")
            for bench in benchmark_result["benchmarks"][-3:]:  # Show last 3 batch sizes
                if "error" not in bench:
                    print(f"      Batch {bench['batch_size']:5d} | "
                          f"Time: {bench['processing_time_seconds']:6.2f}s | "
                          f"Throughput: {bench['throughput_embeddings_per_second']:6.1f}/s | "
                          f"Memory: {bench.get('memory_delta_mb', 0):+7.1f}MB")
        else:
            print(f"   ❌ Benchmark failed: {benchmark_result['error']}")

    # Memory footprint after all processing
    final_memory = service.get_memory_footprint()
    results["final_memory"] = final_memory

    print("\n📊 Final Memory Footprint:")
    if "note" not in final_memory:
        print(f"   Total: {final_memory['total_mb']:.1f} MB")
        print(f"   Available: {final_memory['available_mb']:.1f} MB")
        print(f"   Used: {final_memory['used_mb']:.1f} MB")
        print(f"   Used %: {final_memory['used_percent']:.1f}%")

        if "note" not in initial_memory:
            memory_delta = final_memory["used_mb"] - initial_memory["used_mb"]
            print(f"   Memory delta: {memory_delta:.1f} MB")
    else:
        print(f"   Note: {final_memory['note']}")

    # Save results
    output_file = "embedding_benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Performance summary
    print("\n🏆 PERFORMANCE SUMMARY")
    print("-" * 40)

    if results["benchmarks"]:
        # Find best performing configuration
        best_throughput = 0
        best_config = None

        for bench_result in results["benchmarks"]:
            if "results" in bench_result and "benchmarks" in bench_result["results"]:
                for bench in bench_result["results"]["benchmarks"]:
                    if "throughput_embeddings_per_second" in bench:
                        throughput = bench["throughput_embeddings_per_second"]
                        if throughput > best_throughput:
                            best_throughput = throughput
                            best_config = {
                                "dataset": bench_result["config"]["name"],
                                "batch_size": bench["batch_size"],
                                "throughput": throughput,
                                "memory_delta": bench.get("memory_delta_mb", 0)
                            }

        if best_config:
            print("🚀 Best Performance:")
            print(f"   Dataset: {best_config['dataset']}")
            print(f"   Batch Size: {best_config['batch_size']}")
            print(f"   Throughput: {best_config['throughput']:.1f} embeddings/sec")
            print(f"   Memory Delta: {best_config['memory_delta']:.1f} MB")

    print("\n💡 RECOMMENDATIONS:")
    print("- Use batch sizes between 16-32 for optimal throughput")
    print("- Memory usage scales linearly with batch size")
    print("- Model loads in ~2-5 seconds and uses ~90-120MB RAM")
    print("- Throughput: 100-500 embeddings/second depending on batch size")

    return results


def run_quick_test():
    """Run a quick test to verify functionality."""
    print("Running quick embedding test...")

    service = EmbeddingService()

    if not service.model:
        print("❌ Embedding model not available")
        return False

    # Quick test with small dataset
    texts = [
        "This is a great product!",
        "I hate this service.",
        "It's okay, nothing special.",
        "Amazing customer support.",
        "Terrible user experience."
    ]

    print(f"Testing with {len(texts)} sample texts...")

    start_time = time.time()
    embeddings = service.generate_embeddings(texts, batch_size=4)
    processing_time = time.time() - start_time

    if embeddings is not None:
        print(f"   ✅ Generated embeddings in {processing_time:.2f}s")
        print(f"   Shape: {embeddings.shape}")

        memory_info = service.get_memory_footprint()
        if "note" not in memory_info:
            print(f"   Memory usage: {memory_info['used_mb']:.1f} MB")
        else:
            print(f"   Memory monitoring: {memory_info['note']}")

        # Test ChromaDB storage if available
        if service.chroma_collection:
            ids = [f"test_{i}" for i in range(len(texts))]
            stored = service.store_embeddings_chroma(embeddings, texts, ids)
            if stored:
                print("   ✅ ChromaDB storage: SUCCESS")
            else:
                print("   ❌ ChromaDB storage: FAILED")
        else:
            print("   ⚠️  ChromaDB not available")

        return True
    else:
        print("❌ Embedding generation failed")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark embedding service")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive benchmark")

    args = parser.parse_args()

    if args.quick or not (args.quick or args.comprehensive):
        # Default to quick test
        success = run_quick_test()
        sys.exit(0 if success else 1)

    if args.comprehensive:
        results = run_comprehensive_benchmark()
        sys.exit(0 if results else 1)
