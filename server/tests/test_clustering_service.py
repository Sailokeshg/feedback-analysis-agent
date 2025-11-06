"""
Unit tests for clustering service - HDBSCAN, UMAP, keyword extraction.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.services.clustering_service import ClusteringService


class TestClusteringService:
    """Test clustering service functionality."""

    def test_initialization_with_available_dependencies(self):
        """Test service initialization when all dependencies are available."""
        with patch('app.services.clustering_service.hdbscan') as mock_hdbscan, \
             patch('app.services.clustering_service.umap') as mock_umap, \
             patch('app.services.clustering_service.sklearn') as mock_sklearn, \
             patch('app.services.clustering_service.yake') as mock_yake, \
             patch('app.services.clustering_service.nltk') as mock_nltk:

            mock_hdbscan.HDBSCAN = Mock()
            mock_umap.UMAP = Mock()
            mock_sklearn.TfidfVectorizer = Mock()
            mock_sklearn.KMeans = Mock()
            mock_yake.KeywordExtractor = Mock()
            mock_nltk.stopwords = Mock()
            mock_nltk.word_tokenize = Mock()

            service = ClusteringService()

            assert service.hdbscan_available
            assert service.umap_available
            assert service.sklearn_available
            assert service.yake_available
            assert service.nltk_available

    def test_initialization_without_dependencies(self):
        """Test service initialization when dependencies are not available."""
        with patch('app.services.clustering_service.hdbscan', None), \
             patch('app.services.clustering_service.umap', None), \
             patch('app.services.clustering_service.sklearn', None), \
             patch('app.services.clustering_service.yake', None), \
             patch('app.services.clustering_service.nltk', None):

            service = ClusteringService()

            assert not service.hdbscan_available
            assert not service.umap_available
            assert not service.sklearn_available
            assert not service.yake_available
            assert not service.nltk_available

    @patch('app.services.clustering_service.ClusteringService._initialize_clustering_libs')
    def test_cluster_texts_empty(self, mock_init):
        """Test clustering with empty text list."""
        mock_init.return_value = None
        service = ClusteringService()

        clusters, embeddings, reduced = service.cluster_texts([])
        assert clusters == {"cluster_0": []}
        assert embeddings.size == 0
        assert reduced is None

    @patch('app.services.clustering_service.ClusteringService._initialize_clustering_libs')
    def test_cluster_texts_single_item(self, mock_init):
        """Test clustering with single text item."""
        mock_init.return_value = None
        service = ClusteringService()

        # Mock embedding generation
        service.generate_embeddings = Mock(return_value=np.array([[0.1, 0.2, 0.3]]))

        clusters, embeddings, reduced = service.cluster_texts(["single text"])
        assert clusters == {"cluster_0": [0]}
        assert embeddings.shape == (1, 3)
        assert reduced is None

    @patch('app.services.clustering_service.ClusteringService._initialize_clustering_libs')
    def test_cluster_texts_hdbscan(self, mock_init):
        """Test HDBSCAN clustering."""
        mock_init.return_value = None
        service = ClusteringService()
        service.hdbscan_available = True

        # Mock dependencies
        service.generate_embeddings = Mock(return_value=np.random.rand(10, 384))
        service.embedding_service.store_embeddings_chroma = Mock()

        # Mock HDBSCAN
        mock_clusterer = Mock()
        mock_clusterer.fit_predict.return_value = [0, 0, 1, 1, -1, -1, 2, 2, 2, -1]  # 3 clusters + noise

        with patch('app.services.clustering_service.hdbscan') as mock_hdbscan:
            mock_hdbscan.HDBSCAN.return_value = mock_clusterer

            clusters, embeddings, reduced = service.cluster_texts(
                ["text"] * 10, use_umap=False
            )

            assert len(clusters) > 0  # Should have clusters
            assert embeddings.shape == (10, 384)
            assert reduced is None  # No UMAP

    @patch('app.services.clustering_service.ClusteringService._initialize_clustering_libs')
    def test_cluster_texts_kmeans_fallback(self, mock_init):
        """Test k-means fallback for small datasets."""
        mock_init.return_value = None
        service = ClusteringService()
        service.hdbscan_available = False
        service.sklearn_available = True

        # Mock dependencies
        service.generate_embeddings = Mock(return_value=np.random.rand(50, 384))
        service.embedding_service.store_embeddings_chroma = Mock()

        # Mock k-means
        mock_kmeans = Mock()
        mock_kmeans.fit_predict.return_value = [0] * 25 + [1] * 25

        with patch('app.services.clustering_service.sklearn') as mock_sklearn:
            mock_sklearn.KMeans.return_value = mock_kmeans

            clusters, embeddings, reduced = service.cluster_texts(
                ["text"] * 50, use_umap=False
            )

            assert len(clusters) == 2  # Should have 2 clusters
            assert embeddings.shape == (50, 384)

    def test_extract_keywords_empty(self):
        """Test keyword extraction with empty input."""
        service = ClusteringService()
        keywords = service.extract_keywords([])
        assert keywords == []

    def test_extract_keywords_yake(self):
        """Test YAKE keyword extraction."""
        service = ClusteringService()
        service.yake_available = True

        # Mock YAKE
        mock_extractor = Mock()
        mock_extractor.extract_keywords.return_value = [
            ("machine learning", 0.8),
            ("artificial intelligence", 0.7),
            ("data science", 0.6)
        ]

        with patch.object(service, 'yake') as mock_yake:
            mock_yake.KeywordExtractor.return_value = mock_extractor

            keywords = service.extract_keywords(["ML and AI are key technologies."], max_keywords=2)
            assert keywords == ["machine learning", "artificial intelligence"]

    def test_extract_keywords_ngrams(self):
        """Test n-gram TF-IDF keyword extraction."""
        service = ClusteringService()
        service.yake_available = False
        service.sklearn_available = True
        service.nltk_available = True

        # Mock sklearn components
        mock_vectorizer = Mock()
        mock_vectorizer.fit_transform.return_value = Mock()
        mock_vectorizer.get_feature_names_out.return_value = [
            "machine", "learning", "artificial", "intelligence", "data", "science"
        ]
        mock_matrix = Mock()
        mock_matrix.toarray.return_value = [[0.8, 0.7, 0.6, 0.5, 0.4, 0.3]]

        with patch('app.services.clustering_service.sklearn') as mock_sklearn:
            mock_sklearn.TfidfVectorizer.return_value = mock_vectorizer
            mock_vectorizer.fit_transform.return_value = mock_matrix

            keywords = service.extract_keywords(["ML and AI are key."], max_keywords=3)
            assert len(keywords) <= 3

    def test_extract_keywords_simple_fallback(self):
        """Test simple frequency-based keyword extraction fallback."""
        service = ClusteringService()
        service.yake_available = False
        service.sklearn_available = False
        service.nltk_available = True

        # Mock NLTK
        with patch('app.services.clustering_service.nltk') as mock_nltk:
            mock_stopwords = Mock()
            mock_stopwords.words.return_value = ['the', 'and', 'or', 'but']
            mock_nltk.stopwords.words = mock_stopwords.words

            keywords = service.extract_keywords(["the machine learning and artificial intelligence"], max_keywords=2)
            assert len(keywords) <= 2
            assert "machine" in keywords[0].lower() or "learning" in keywords[0].lower()

    def test_cluster_texts_with_keywords(self):
        """Test full clustering pipeline with keyword extraction."""
        service = ClusteringService()

        # Mock the core methods
        mock_clusters = {"cluster_0": [0, 1], "cluster_1": [2, 3]}
        service.cluster_texts = Mock(return_value=(mock_clusters, np.random.rand(4, 384), None))
        service.extract_keywords = Mock(return_value=["keyword1", "keyword2"])

        result = service.cluster_texts_with_keywords(["text"] * 4)

        assert len(result) == 2
        assert "cluster_0" in result
        assert "cluster_1" in result
        assert "keywords" in result["cluster_0"]
        assert "label" in result["cluster_0"]

    def test_preprocess_text(self):
        """Test text preprocessing for keyword extraction."""
        service = ClusteringService()

        text = "Hello @user! Check https://example.com and email@test.com"
        processed = service._preprocess_text(text)

        assert "@user" not in processed
        assert "https://" not in processed
        assert "@test.com" not in processed
        assert processed == processed.lower()

    def test_generate_cluster_label(self):
        """Test cluster label generation."""
        service = ClusteringService()

        # Test with multiple keywords
        label = service._generate_cluster_label(["price", "cost", "expensive"], [])
        assert label == "Price, cost, expensive"

        # Test with single keyword
        label = service._generate_cluster_label(["shipping"], [])
        assert label == "Shipping"

        # Test with empty keywords
        label = service._generate_cluster_label([], [])
        assert label == "Miscellaneous"

    def test_umap_integration(self):
        """Test UMAP dimensionality reduction integration."""
        service = ClusteringService()
        service.umap_available = True

        # Mock UMAP
        mock_umap_instance = Mock()
        mock_umap_instance.fit_transform.return_value = np.random.rand(10, 5)

        with patch('app.services.clustering_service.umap') as mock_umap:
            mock_umap.UMAP.return_value = mock_umap_instance

            # Mock other dependencies
            service.generate_embeddings = Mock(return_value=np.random.rand(10, 384))
            service.embedding_service.store_embeddings_chroma = Mock()
            service._cluster_hdbscan = Mock(return_value={"cluster_0": list(range(10))})

            clusters, embeddings, reduced = service.cluster_texts(
                ["text"] * 10, use_umap=True
            )

            assert reduced is not None
            assert reduced.shape == (10, 5)
            mock_umap_instance.fit_transform.assert_called_once()

    def test_fallback_strategies(self):
        """Test graceful fallback when algorithms are unavailable."""
        service = ClusteringService()

        # Disable all advanced algorithms
        service.hdbscan_available = False
        service.umap_available = False
        service.sklearn_available = False
        service.yake_available = False
        service.nltk_available = False

        # Should still work with basic similarity clustering
        service.generate_embeddings = Mock(return_value=np.random.rand(5, 384))
        service.embedding_service.store_embeddings_chroma = Mock()

        clusters, embeddings, reduced = service.cluster_texts(["text"] * 5)

        assert len(clusters) > 0
        assert embeddings.shape == (5, 384)

    def test_error_handling_clustering(self):
        """Test error handling in clustering algorithms."""
        service = ClusteringService()
        service.hdbscan_available = True

        # Mock failed HDBSCAN
        with patch('app.services.clustering_service.hdbscan') as mock_hdbscan:
            mock_hdbscan.HDBSCAN.side_effect = Exception("HDBSCAN failed")

            service.generate_embeddings = Mock(return_value=np.random.rand(10, 384))
            service.embedding_service.store_embeddings_chroma = Mock()

            # Should fall back to similarity clustering
            clusters, embeddings, reduced = service.cluster_texts(["text"] * 10)

            assert len(clusters) > 0  # Should still produce some clusters

    def test_batch_processing_memory_efficiency(self):
        """Test that batch processing handles large datasets efficiently."""
        service = ClusteringService()

        # Mock embedding generation to simulate large dataset
        large_embeddings = np.random.rand(1000, 384)
        service.generate_embeddings = Mock(return_value=large_embeddings)
        service.embedding_service.store_embeddings_chroma = Mock()

        # Mock HDBSCAN for large dataset
        service.hdbscan_available = True
        mock_clusterer = Mock()
        mock_clusterer.fit_predict.return_value = [0] * 500 + [1] * 500

        with patch('app.services.clustering_service.hdbscan') as mock_hdbscan:
            mock_hdbscan.HDBSCAN.return_value = mock_clusterer

            clusters, embeddings, reduced = service.cluster_texts(
                ["text"] * 1000, use_umap=False
            )

            assert embeddings.shape == (1000, 384)
            assert len(clusters) == 2

    def test_keyword_extraction_edge_cases(self):
        """Test keyword extraction with various edge cases."""
        service = ClusteringService()

        # Test with very short texts
        keywords = service.extract_keywords(["ok", "yes", "no"], max_keywords=5)
        assert isinstance(keywords, list)

        # Test with very long text
        long_text = "word " * 1000
        keywords = service.extract_keywords([long_text], max_keywords=3)
        assert len(keywords) <= 3

        # Test with special characters
        special_text = "C++ JavaScript @user #hashtag https://url.com"
        keywords = service.extract_keywords([special_text], max_keywords=5)
        assert isinstance(keywords, list)
        # Should not contain URLs, mentions, etc.
        for keyword in keywords:
            assert "https://" not in keyword
            assert "@" not in keyword
            assert "#" not in keyword
