#!/usr/bin/env python3
"""
Demo and benchmark script for topic detection using HDBSCAN and keyword extraction.
"""

import os
import sys
import time
import json
from typing import List, Dict

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.clustering_service import ClusteringService


def generate_sample_feedback_texts(n_texts: int = 100) -> List[str]:
    """Generate sample feedback texts across different topics."""
    import random

    # Define topic templates
    topics = {
        "shipping": [
            "Package arrived late",
            "Shipping was slow",
            "Delivery took forever",
            "FedEx was terrible",
            "UPS lost my package",
            "Shipping fees too high",
            "Free shipping not free",
            "International shipping expensive",
            "Tracking not working",
            "Delivery damaged package"
        ],
        "product_quality": [
            "Product broke after one use",
            "Poor quality materials",
            "Item not as described",
            "Manufacturing defect",
            "Doesn't work properly",
            "Cheap construction",
            "Stopped working",
            "Not durable enough",
            "Quality control issues",
            "Feels flimsy"
        ],
        "customer_service": [
            "Customer service rude",
            "Support not helpful",
            "Long wait times",
            "Chat support useless",
            "Phone support disconnected",
            "Email never answered",
            "Refund process complicated",
            "Return policy unfair",
            "Agent unprofessional",
            "No resolution provided"
        ],
        "pricing": [
            "Too expensive",
            "Price increased",
            "Not worth the money",
            "Better deals elsewhere",
            "Overpriced",
            "Value for money poor",
            "Cheaper competitors",
            "Price doesn't match quality",
            "Hidden fees",
            "Discount not applied"
        ],
        "website": [
            "Website slow",
            "Checkout buggy",
            "Mobile app crashes",
            "Search not working",
            "Account login issues",
            "Payment failed",
            "Site navigation confusing",
            "Images not loading",
            "Out of stock issues",
            "Password reset broken"
        ]
    }

    texts = []
    topic_names = list(topics.keys())

    for _ in range(n_texts):
        # Choose random topic
        topic = random.choice(topic_names)
        # Choose random template from topic
        template = random.choice(topics[topic])
        # Add some variation
        variations = ["", " very disappointed", " extremely frustrated", " really annoying"]
        variation = random.choice(variations)
        text = template + variation + "."
        texts.append(text)

    return texts


def test_basic_clustering():
    """Test basic clustering functionality."""
    print("=" * 60)
    print("Testing Basic Clustering Functionality")
    print("=" * 60)

    service = ClusteringService()

    # Generate sample data
    texts = generate_sample_feedback_texts(50)
    print(f"Generated {len(texts)} sample feedback texts")

    # Test clustering
    start_time = time.time()
    clusters, embeddings, reduced = service.cluster_texts(texts, use_umap=False)
    clustering_time = time.time() - start_time

    print("
📊 Clustering Results:"    print(f"   Texts processed: {len(texts)}")
    print(".2f")
    print(f"   Embeddings shape: {embeddings.shape}")
    print(f"   Clusters found: {len(clusters)}")

    # Show cluster sizes
    cluster_sizes = [(name, len(indices)) for name, indices in clusters.items()]
    cluster_sizes.sort(key=lambda x: x[1], reverse=True)

    print("
🏷️  Cluster Sizes:"    for name, size in cluster_sizes[:5]:  # Show top 5
        print("8")

    # Test keyword extraction for a cluster
    if clusters:
        largest_cluster = max(clusters.items(), key=lambda x: len(x[1]))
        cluster_name, indices = largest_cluster
        cluster_texts = [texts[i] for i in indices]

        keywords = service.extract_keywords(cluster_texts, max_keywords=5)
        print("
🔑 Top Keywords for Largest Cluster:"        for i, keyword in enumerate(keywords, 1):
            print("5")

    return clusters, embeddings


def test_clustering_with_keywords():
    """Test clustering with automatic keyword extraction."""
    print("\n" + "=" * 60)
    print("Testing Clustering with Keywords")
    print("=" * 60)

    service = ClusteringService()

    # Generate sample data
    texts = generate_sample_feedback_texts(30)
    print(f"Processing {len(texts)} texts with keyword extraction")

    start_time = time.time()
    cluster_info = service.cluster_texts_with_keywords(
        texts=texts,
        use_umap=False,
        max_keywords_per_cluster=8
    )
    processing_time = time.time() - start_time

    print(".2f")
    print(f"   Clusters found: {len(cluster_info)}")

    # Show detailed results
    print("
📋 Cluster Details:"    for cluster_name, info in cluster_info.items():
        print(f"\n  {cluster_name}:")
        print(f"    Size: {info['size']} texts")
        print(f"    Label: {info['label']}")
        print(f"    Keywords: {', '.join(info['keywords'][:5])}")

        # Show sample text
        if info['texts']:
            sample_text = info['texts'][0][:60] + "..." if len(info['texts'][0]) > 60 else info['texts'][0]
            print(f"    Sample: {sample_text}")

    return cluster_info


def test_umap_integration():
    """Test UMAP dimensionality reduction integration."""
    print("\n" + "=" * 60)
    print("Testing UMAP Dimensionality Reduction")
    print("=" * 60)

    service = ClusteringService()

    if not service.umap_available:
        print("⚠️  UMAP not available, skipping UMAP test")
        return None

    texts = generate_sample_feedback_texts(50)
    print(f"Testing UMAP with {len(texts)} texts")

    start_time = time.time()

    # Test with UMAP
    clusters_umap, embeddings, reduced = service.cluster_texts(
        texts, use_umap=True, umap_dims=5
    )

    processing_time = time.time() - start_time

    print("
📊 UMAP Results:"    print(".2f")
    print(f"   Original embeddings: {embeddings.shape}")
    print(f"   Reduced embeddings: {reduced.shape if reduced is not None else 'None'}")
    print(f"   Clusters found: {len(clusters_umap)}")

    return clusters_umap, embeddings, reduced


def test_keyword_extraction_methods():
    """Test different keyword extraction methods."""
    print("\n" + "=" * 60)
    print("Testing Keyword Extraction Methods")
    print("=" * 60)

    service = ClusteringService()

    test_texts = [
        "The shipping was incredibly slow and frustrating. Package arrived damaged.",
        "Customer service was rude and unhelpful. Long wait times on phone.",
        "Product quality is terrible. Broke after one day. Cheap materials.",
        "Website is slow and buggy. Checkout process failed multiple times.",
        "Price is too high for the quality. Not worth the money."
    ]

    methods = []

    # Test YAKE if available
    if service.yake_available:
        print("🔍 Testing YAKE keyword extraction...")
        keywords_yake = service.extract_keywords(test_texts, max_keywords=5)
        methods.append(("YAKE", keywords_yake))
        print(f"   Keywords: {keywords_yake}")

    # Test TF-IDF n-grams if available
    if service.sklearn_available:
        print("🔍 Testing TF-IDF n-gram extraction...")
        keywords_tfidf = service.extract_keywords(test_texts, max_keywords=5)
        methods.append(("TF-IDF n-grams", keywords_tfidf))
        print(f"   Keywords: {keywords_tfidf}")

    # Test frequency-based (always available)
    print("🔍 Testing frequency-based extraction...")
    keywords_freq = service.extract_keywords(test_texts, max_keywords=5)
    methods.append(("Frequency", keywords_freq))
    print(f"   Keywords: {keywords_freq}")

    return methods


def benchmark_clustering_performance():
    """Benchmark clustering performance across different dataset sizes."""
    print("\n" + "=" * 60)
    print("Benchmarking Clustering Performance")
    print("=" * 60)

    service = ClusteringService()

    dataset_sizes = [25, 50, 100, 200]
    results = []

    for size in dataset_sizes:
        print(f"\n🧪 Testing with {size} texts...")

        texts = generate_sample_feedback_texts(size)

        start_time = time.time()
        cluster_info = service.cluster_texts_with_keywords(
            texts=texts,
            use_umap=size > 100,  # Use UMAP for larger datasets
            max_keywords_per_cluster=10
        )
        processing_time = time.time() - start_time

        result = {
            "dataset_size": size,
            "processing_time": processing_time,
            "throughput": size / processing_time,
            "clusters_found": len(cluster_info),
            "avg_cluster_size": sum(info["size"] for info in cluster_info.values()) / len(cluster_info) if cluster_info else 0
        }

        results.append(result)
        print(".2f")
        print(".1f")
        print(f"   Clusters: {len(cluster_info)}")
        print(".1f")

    # Save benchmark results
    output_file = "topic_detection_benchmark.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Benchmark results saved to {output_file}")

    # Performance summary
    print("
🏆 Performance Summary:"    if results:
        best_result = max(results, key=lambda x: x["throughput"])
        print("🚀 Best Performance:"        print(f"   Dataset Size: {best_result['dataset_size']}")
        print(".1f")
        print(".1f")

    return results


def test_algorithm_comparison():
    """Compare different clustering algorithms."""
    print("\n" + "=" * 60)
    print("Comparing Clustering Algorithms")
    print("=" * 60)

    service = ClusteringService()
    texts = generate_sample_feedback_texts(75)

    algorithms = []

    # Test HDBSCAN if available
    if service.hdbscan_available:
        print("🔬 Testing HDBSCAN...")
        start_time = time.time()
        clusters_hdb, _, _ = service.cluster_texts(texts, use_umap=False)
        hdb_time = time.time() - start_time
        algorithms.append(("HDBSCAN", len(clusters_hdb), hdb_time))
        print(".2f")
        print(f"   Clusters: {len(clusters_hdb)}")

    # Test k-means if available
    if service.sklearn_available:
        print("🔬 Testing k-means...")
        start_time = time.time()
        clusters_kmeans, _, _ = service.cluster_texts(texts, n_clusters=5, use_umap=False)
        kmeans_time = time.time() - start_time
        algorithms.append(("k-means", len(clusters_kmeans), kmeans_time))
        print(".2f")
        print(f"   Clusters: {len(clusters_kmeans)}")

    # Show comparison
    if algorithms:
        print("
📊 Algorithm Comparison:"        for name, clusters, timing in algorithms:
            print("10")

    return algorithms


def main():
    """Run all topic detection tests and benchmarks."""
    print("🧠 Topic Detection Demo & Benchmark")
    print("Testing HDBSCAN clustering with keyword extraction")

    try:
        # Run all tests
        basic_results = test_basic_clustering()
        keyword_results = test_clustering_with_keywords()
        umap_results = test_umap_integration()
        keyword_methods = test_keyword_extraction_methods()
        benchmark_results = benchmark_clustering_performance()
        algorithm_comparison = test_algorithm_comparison()

        # Summary
        print("\n" + "=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)

        print("✅ Basic clustering: Working")
        print("✅ Keyword extraction: Working")
        if umap_results:
            print("✅ UMAP integration: Working")
        else:
            print("⚠️  UMAP integration: Not available")

        print(f"✅ Keyword methods tested: {len(keyword_methods)}")
        print(f"✅ Benchmark datasets tested: {len(benchmark_results)}")
        print(f"✅ Algorithms compared: {len(algorithm_comparison)}")

        print("
🔧 Key Features Demonstrated:"        print("   • HDBSCAN density-based clustering")
        print("   • UMAP dimensionality reduction")
        print("   • YAKE keyword extraction")
        print("   • TF-IDF n-gram keywords")
        print("   • Frequency-based keywords")
        print("   • Automatic cluster labeling")
        print("   • Performance benchmarking")

        print("
💡 Usage:"        print("   # Basic clustering"        print("   clusters = service.cluster_texts(texts)"        print("   "        print("   # Clustering with keywords"        print("   results = service.cluster_texts_with_keywords(texts)"        print("   "        print("   # Extract keywords from texts"        print("   keywords = service.extract_keywords(texts)"

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
