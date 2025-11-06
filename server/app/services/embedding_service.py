"""
Embedding service for generating and managing text embeddings.
Uses sentence-transformers/all-MiniLM-L6-v2 with batch processing and CPU fallback.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, embeddings disabled")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not available, vector storage disabled")


class EmbeddingService:
    """Service for generating and managing text embeddings."""

    # Model configuration
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2
    MAX_SEQ_LENGTH = 256  # Maximum sequence length for truncation
    BATCH_SIZE = 32  # Default batch size for processing

    def __init__(self):
        self.model = None
        self.chroma_client = None
        self.chroma_collection = None
        self._initialize_model()
        self._initialize_chroma()

    def _initialize_model(self):
        """Initialize the sentence transformer model with CPU fallback."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("Cannot initialize embedding model: sentence-transformers not available")
            return

        try:
            # Force CPU usage for consistency and cost control
            device = "cpu"
            logger.info(f"Loading sentence-transformers model: {self.MODEL_NAME} on {device}")

            # Record memory before loading (if available)
            memory_before = None
            if PSUTIL_AVAILABLE:
                memory_before = psutil.virtual_memory().used / 1024 / 1024  # MB

            start_time = time.time()
            self.model = SentenceTransformer(self.MODEL_NAME, device=device)

            # Configure model settings
            self.model.max_seq_length = self.MAX_SEQ_LENGTH

            load_time = time.time() - start_time

            memory_info = ""
            if PSUTIL_AVAILABLE and memory_before is not None:
                memory_after = psutil.virtual_memory().used / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before
                memory_info = f"Memory delta: {memory_delta:.1f}MB. "

            logger.info(
                f"Model loaded successfully in {load_time:.2f}s. "
                f"{memory_info}"
                f"Max sequence length: {self.MAX_SEQ_LENGTH}"
            )

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not available, skipping vector store initialization")
            return

        try:
            # Use persistent storage
            chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)

            # Create or get collection for feedback embeddings
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="feedback_embeddings",
                metadata={"dimension": self.EMBEDDING_DIMENSION}
            )

            logger.info(f"ChromaDB initialized with collection 'feedback_embeddings' at {chroma_path}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings for a list of texts using batch processing.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing (default: class default)
            show_progress: Whether to show progress bar

        Returns:
            Numpy array of embeddings or None if failed
        """
        if not self.model:
            logger.error("Embedding model not available")
            return None

        if not texts:
            return np.array([]).reshape(0, self.EMBEDDING_DIMENSION)

        batch_size = batch_size or self.BATCH_SIZE

        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts with batch size {batch_size}")

            # Record timing and memory
            start_time = time.time()
            memory_before = None
            if PSUTIL_AVAILABLE:
                memory_before = psutil.virtual_memory().used / 1024 / 1024  # MB

            # Process in batches to manage memory
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

                # Generate embeddings for this batch
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=show_progress and len(batch_texts) > 10
                )
                all_embeddings.append(batch_embeddings)

            # Concatenate all batches
            embeddings = np.concatenate(all_embeddings, axis=0)

            # Record metrics
            processing_time = time.time() - start_time

            memory_info = ""
            if PSUTIL_AVAILABLE and memory_before is not None:
                memory_after = psutil.virtual_memory().used / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before
                memory_info = f"Memory delta: {memory_delta:.1f}MB. "

            logger.info(
                f"Generated {len(embeddings)} embeddings in {processing_time:.2f}s "
                f"({len(embeddings)/processing_time:.1f} embeddings/sec). "
                f"{memory_info}"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return None

    def store_embeddings_chroma(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Store embeddings in ChromaDB for vector search.

        Args:
            embeddings: Numpy array of embeddings
            texts: Original text documents
            ids: Unique IDs for each document
            metadata: Optional metadata for each document

        Returns:
            True if successful, False otherwise
        """
        if not self.chroma_collection:
            logger.warning("ChromaDB not available, skipping vector storage")
            return False

        try:
            # Prepare data for ChromaDB
            embeddings_list = embeddings.tolist()
            documents = texts
            metadatas = metadata or [{}] * len(texts)

            # Add to collection
            self.chroma_collection.add(
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.debug(f"Stored {len(embeddings)} embeddings in ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Failed to store embeddings in ChromaDB: {e}")
            return False

    def search_similar(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in ChromaDB.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filters

        Returns:
            List of similar documents with distances
        """
        if not self.chroma_collection:
            logger.warning("ChromaDB not available for similarity search")
            return []

        try:
            # Query ChromaDB
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )

            # Format results
            similar_docs = []
            if results['documents'] and results['distances']:
                for doc, distance, metadata, id in zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0],
                    results['ids'][0]
                ):
                    similar_docs.append({
                        "id": id,
                        "text": doc,
                        "distance": distance,
                        "metadata": metadata
                    })

            return similar_docs

        except Exception as e:
            logger.error(f"Failed to search similar embeddings: {e}")
            return []

    def benchmark_embedding_generation(
        self,
        texts: List[str],
        batch_sizes: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Benchmark embedding generation performance.

        Args:
            texts: List of texts to embed
            batch_sizes: Different batch sizes to test

        Returns:
            Benchmark results
        """
        if not self.model:
            return {"error": "Model not available"}

        batch_sizes = batch_sizes or [1, 8, 16, 32, 64]

        results = {
            "model": self.MODEL_NAME,
            "dimension": self.EMBEDDING_DIMENSION,
            "max_seq_length": self.MAX_SEQ_LENGTH,
            "num_texts": len(texts),
            "benchmarks": []
        }

        for batch_size in batch_sizes:
            logger.info(f"Benchmarking with batch size {batch_size}")

            start_time = time.time()
            memory_before = None
            if PSUTIL_AVAILABLE:
                memory_before = psutil.virtual_memory().used / 1024 / 1024  # MB

            embeddings = self.generate_embeddings(texts, batch_size=batch_size, show_progress=False)

            processing_time = time.time() - start_time

            if embeddings is not None:
                throughput = len(texts) / processing_time
                memory_delta = 0
                if PSUTIL_AVAILABLE and memory_before is not None:
                    memory_after = psutil.virtual_memory().used / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before

                results["benchmarks"].append({
                    "batch_size": batch_size,
                    "processing_time_seconds": processing_time,
                    "throughput_embeddings_per_second": throughput,
                    "memory_delta_mb": memory_delta,
                    "peak_memory_mb": memory_peak
                })
            else:
                results["benchmarks"].append({
                    "batch_size": batch_size,
                    "error": "Embedding generation failed"
                })

        return results

    def get_memory_footprint(self) -> Dict[str, float]:
        """Get current memory footprint information."""
        if not PSUTIL_AVAILABLE:
            return {
                "total_mb": 0,
                "available_mb": 0,
                "used_mb": 0,
                "used_percent": 0,
                "note": "psutil not available"
            }

        memory = psutil.virtual_memory()
        return {
            "total_mb": memory.total / 1024 / 1024,
            "available_mb": memory.available / 1024 / 1024,
            "used_mb": memory.used / 1024 / 1024,
            "used_percent": memory.percent
        }
