"""
Unit tests for embedding service - generation, storage, and retrieval.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from app.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test embedding service functionality."""

    def test_initialization_with_available_dependencies(self):
        """Test service initialization when all dependencies are available."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('app.services.embedding_service.CHROMA_AVAILABLE', True):

            with patch('sentence_transformers.SentenceTransformer') as mock_model_class, \
                 patch('chromadb.PersistentClient') as mock_chroma_client:

                # Mock the model
                mock_model = Mock()
                mock_model_class.return_value = mock_model

                # Mock ChromaDB
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chroma_client.return_value = mock_client

                service = EmbeddingService()

                assert service.model is not None
                assert service.chroma_client is not None
                assert service.chroma_collection is not None

    def test_initialization_without_dependencies(self):
        """Test service initialization when dependencies are not available."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', False), \
             patch('app.services.embedding_service.CHROMA_AVAILABLE', False):

            service = EmbeddingService()

            assert service.model is None
            assert service.chroma_client is None
            assert service.chroma_collection is None

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('app.services.embedding_service.CHROMA_AVAILABLE', True)
    def test_generate_embeddings_success(self):
        """Test successful embedding generation."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model_class:
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(3, 384)
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            texts = ["Hello world", "Test text", "Another example"]
            embeddings = service.generate_embeddings(texts)

            assert embeddings is not None
            assert embeddings.shape == (3, 384)
            mock_model.encode.assert_called_once()

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    def test_generate_embeddings_no_model(self):
        """Test embedding generation when model is not available."""
        service = EmbeddingService()
        service.model = None

        texts = ["Hello world"]
        embeddings = service.generate_embeddings(texts)

        assert embeddings is None

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    def test_generate_embeddings_empty_texts(self):
        """Test embedding generation with empty text list."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model_class:
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            embeddings = service.generate_embeddings([])

            assert embeddings is not None
            assert embeddings.shape == (0, 384)
            mock_model.encode.assert_not_called()

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('app.services.embedding_service.CHROMA_AVAILABLE', True)
    def test_store_embeddings_chroma_success(self):
        """Test successful storage in ChromaDB."""
        with patch('chromadb.PersistentClient') as mock_chroma_client:
            mock_client = Mock()
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chroma_client.return_value = mock_client

            service = EmbeddingService()
            service.chroma_collection = mock_collection

            embeddings = np.random.rand(2, 384)
            texts = ["text1", "text2"]
            ids = ["id1", "id2"]

            result = service.store_embeddings_chroma(embeddings, texts, ids)

            assert result is True
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args
            assert len(call_args[1]['embeddings']) == 2
            assert call_args[1]['documents'] == texts
            assert call_args[1]['ids'] == ids

    @patch('app.services.embedding_service.CHROMA_AVAILABLE', True)
    def test_store_embeddings_chroma_no_collection(self):
        """Test ChromaDB storage when collection is not available."""
        service = EmbeddingService()
        service.chroma_collection = None

        embeddings = np.random.rand(1, 384)
        result = service.store_embeddings_chroma(embeddings, ["text"], ["id"])

        assert result is False

    @patch('app.services.embedding_service.CHROMA_AVAILABLE', True)
    def test_search_similar_success(self):
        """Test successful similarity search."""
        with patch('chromadb.PersistentClient') as mock_chroma_client:
            mock_client = Mock()
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chroma_client.return_value = mock_client

            # Mock query results
            mock_collection.query.return_value = {
                'documents': [['doc1', 'doc2']],
                'distances': [[0.1, 0.2]],
                'metadatas': [[{'key': 'value1'}, {'key': 'value2'}]],
                'ids': [['id1', 'id2']]
            }

            service = EmbeddingService()
            service.chroma_collection = mock_collection

            query_embedding = np.random.rand(384)
            results = service.search_similar(query_embedding, n_results=2)

            assert len(results) == 2
            assert results[0]['id'] == 'id1'
            assert results[0]['distance'] == 0.1
            assert results[1]['id'] == 'id2'
            assert results[1]['distance'] == 0.2

    @patch('app.services.embedding_service.CHROMA_AVAILABLE', True)
    def test_search_similar_no_collection(self):
        """Test similarity search when collection is not available."""
        service = EmbeddingService()
        service.chroma_collection = None

        query_embedding = np.random.rand(384)
        results = service.search_similar(query_embedding)

        assert results == []

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    def test_benchmark_embedding_generation(self):
        """Test embedding generation benchmarking."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model_class:
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(10, 384)
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            texts = ["text"] * 10
            results = service.benchmark_embedding_generation(texts, batch_sizes=[1, 5])

            assert "model" in results
            assert "dimension" in results
            assert "benchmarks" in results
            assert len(results["benchmarks"]) == 2

            for benchmark in results["benchmarks"]:
                assert "batch_size" in benchmark
                assert "processing_time_seconds" in benchmark
                assert "throughput_embeddings_per_second" in benchmark

    @patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', False)
    def test_benchmark_no_model(self):
        """Test benchmarking when model is not available."""
        service = EmbeddingService()

        results = service.benchmark_embedding_generation(["text"])
        assert results == {"error": "Model not available"}

    def test_get_memory_footprint(self):
        """Test memory footprint reporting."""
        service = EmbeddingService()

        footprint = service.get_memory_footprint()

        assert "total_mb" in footprint
        assert "available_mb" in footprint
        assert "used_mb" in footprint
        assert "used_percent" in footprint

        # Values should be reasonable
        assert footprint["total_mb"] > 0
        assert footprint["used_percent"] >= 0 and footprint["used_percent"] <= 100

    def test_batch_processing(self):
        """Test that batch processing works correctly."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('sentence_transformers.SentenceTransformer') as mock_model_class:

            mock_model = Mock()
            # Mock encode to return different results for different batch sizes
            def mock_encode(texts, **kwargs):
                batch_size = len(texts)
                return np.random.rand(batch_size, 384)

            mock_model.encode = mock_encode
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            # Test with different batch sizes
            texts = ["text"] * 100

            # Should process in batches of 32 (default)
            embeddings = service.generate_embeddings(texts, batch_size=32)

            assert embeddings is not None
            assert embeddings.shape == (100, 384)

            # Should have been called multiple times for batching
            assert mock_model.encode.call_count > 1

    def test_truncation_handling(self):
        """Test that long texts are properly truncated."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('sentence_transformers.SentenceTransformer') as mock_model_class:

            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(1, 384)
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            # Create a very long text
            long_text = "word " * 1000  # Much longer than max_seq_length
            embeddings = service.generate_embeddings([long_text])

            assert embeddings is not None
            assert embeddings.shape == (1, 384)

            # Verify model was configured with max_seq_length
            assert mock_model.max_seq_length == 256

    def test_error_handling_embedding_generation(self):
        """Test error handling during embedding generation."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
             patch('sentence_transformers.SentenceTransformer') as mock_model_class:

            mock_model = Mock()
            mock_model.encode.side_effect = Exception("Encoding failed")
            mock_model_class.return_value = mock_model

            service = EmbeddingService()
            service.model = mock_model

            embeddings = service.generate_embeddings(["test text"])

            assert embeddings is None

    def test_error_handling_chroma_storage(self):
        """Test error handling during ChromaDB storage."""
        with patch('app.services.embedding_service.CHROMA_AVAILABLE', True), \
             patch('chromadb.PersistentClient') as mock_chroma_client:

            mock_client = Mock()
            mock_collection = Mock()
            mock_collection.add.side_effect = Exception("Storage failed")
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chroma_client.return_value = mock_client

            service = EmbeddingService()
            service.chroma_collection = mock_collection

            embeddings = np.random.rand(1, 384)
            result = service.store_embeddings_chroma(embeddings, ["text"], ["id"])

            assert result is False
