import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
import re
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ClusteringService:
    """Advanced clustering service using HDBSCAN with UMAP and keyword extraction."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._initialize_clustering_libs()

    def _initialize_clustering_libs(self):
        """Initialize clustering libraries with graceful fallbacks."""
        self.hdbscan_available = False
        self.umap_available = False
        self.sklearn_available = False
        self.yake_available = False
        self.nltk_available = False

        # Try to import HDBSCAN
        try:
            import hdbscan
            self.hdbscan = hdbscan
            self.hdbscan_available = True
            logger.info("HDBSCAN initialized successfully")
        except ImportError:
            logger.warning("HDBSCAN not available, will use k-means fallback")
            self.hdbscan = None

        # Try to import UMAP
        try:
            import umap
            self.umap = umap
            self.umap_available = True
            logger.info("UMAP initialized successfully")
        except ImportError:
            logger.warning("UMAP not available, skipping dimensionality reduction")
            self.umap = None

        # Try to import sklearn
        try:
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.sklearn = {
                'KMeans': KMeans,
                'TfidfVectorizer': TfidfVectorizer,
                'cosine_similarity': cosine_similarity
            }
            self.sklearn_available = True
            logger.info("Scikit-learn initialized successfully")
        except ImportError:
            logger.warning("Scikit-learn not available, clustering will be limited")
            self.sklearn = None

        # Try to import YAKE
        try:
            import yake
            self.yake = yake
            self.yake_available = True
            logger.info("YAKE initialized successfully")
        except ImportError:
            logger.warning("YAKE not available, will use n-gram fallback")
            self.yake = None

        # Try to import NLTK
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize, sent_tokenize
            # Download required NLTK data if not present
            try:
                stopwords.words('english')
            except LookupError:
                nltk.download('stopwords', quiet=True)
            try:
                word_tokenize('test')
            except LookupError:
                nltk.download('punkt', quiet=True)

            self.nltk = {
                'stopwords': stopwords,
                'word_tokenize': word_tokenize,
                'sent_tokenize': sent_tokenize
            }
            self.nltk_available = True
            logger.info("NLTK initialized successfully")
        except ImportError:
            logger.warning("NLTK not available, keyword extraction will be limited")
            self.nltk = None

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        return self.embedding_service.generate_embeddings(texts)

    def cluster_texts(
        self,
        texts: List[str],
        n_clusters: Optional[int] = None,
        use_umap: bool = True,
        umap_dims: int = 5
    ) -> Tuple[Dict[str, List[int]], np.ndarray, Optional[np.ndarray]]:
        """
        Cluster texts using embeddings with HDBSCAN or k-means fallback.

        Args:
            texts: List of texts to cluster
            n_clusters: Target number of clusters (used for k-means fallback)
            use_umap: Whether to use UMAP for dimensionality reduction
            umap_dims: Target dimensions for UMAP reduction

        Returns:
            Tuple of (cluster_assignments, embeddings, reduced_embeddings)
            cluster_assignments: Dict mapping cluster names to lists of text indices
            embeddings: Original embeddings array
            reduced_embeddings: UMAP-reduced embeddings (or None if not used)
        """
        if len(texts) < 2:
            return {"cluster_0": list(range(len(texts)))}, np.array([]), None

        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        if embeddings is None or len(embeddings) == 0:
            return {"cluster_0": list(range(len(texts)))}, np.array([]), None

        # Store in Chroma for later retrieval
        ids = [f"cluster_doc_{i}" for i in range(len(texts))]
        self.embedding_service.store_embeddings_chroma(
            embeddings=embeddings,
            texts=texts,
            ids=ids,
            metadata=[{"source": "clustering"} for _ in texts]
        )

        # Apply dimensionality reduction if requested and available
        reduced_embeddings = None
        clustering_embeddings = embeddings

        if use_umap and self.umap_available and len(embeddings) > umap_dims:
            try:
                logger.info(f"Applying UMAP dimensionality reduction to {umap_dims} dimensions")
                umap_reducer = self.umap.UMAP(
                    n_components=umap_dims,
                    n_neighbors=min(15, len(embeddings) - 1),
                    min_dist=0.1,
                    random_state=42
                )
                reduced_embeddings = umap_reducer.fit_transform(embeddings)
                clustering_embeddings = reduced_embeddings
                logger.info(f"UMAP reduction completed: {embeddings.shape} -> {reduced_embeddings.shape}")
            except Exception as e:
                logger.warning(f"UMAP reduction failed: {e}, using original embeddings")
                reduced_embeddings = None
                clustering_embeddings = embeddings

        # Choose clustering algorithm based on dataset size and availability
        if len(texts) < 500 and self.sklearn_available:
            # Use k-means for small datasets
            clusters = self._cluster_kmeans(clustering_embeddings, n_clusters)
        elif self.hdbscan_available:
            # Use HDBSCAN for larger datasets
            clusters = self._cluster_hdbscan(clustering_embeddings)
        elif self.sklearn_available:
            # Fallback to k-means
            clusters = self._cluster_kmeans(clustering_embeddings, n_clusters)
        else:
            # Ultimate fallback: simple similarity-based clustering
            clusters = self._cluster_similarity_threshold(embeddings)

        return clusters, embeddings, reduced_embeddings

    def _cluster_hdbscan(self, embeddings: np.ndarray) -> Dict[str, List[int]]:
        """Cluster using HDBSCAN."""
        try:
            logger.info("Clustering with HDBSCAN")

            # Configure HDBSCAN parameters
            min_cluster_size = max(2, int(len(embeddings) * 0.02))  # 2% of dataset or minimum 2
            min_samples = max(1, min_cluster_size // 2)

            clusterer = self.hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                cluster_selection_epsilon=0.1,
                metric='euclidean'
            )

            cluster_labels = clusterer.fit_predict(embeddings)

            # Group by cluster labels (-1 indicates noise)
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label == -1:
                    # Assign noise points to their own clusters
                    cluster_name = f"noise_{i}"
                else:
                    cluster_name = f"cluster_{label}"

                if cluster_name not in clusters:
                    clusters[cluster_name] = []
                clusters[cluster_name].append(i)

            # Remove clusters with only one item (except noise clusters)
            filtered_clusters = {}
            for cluster_name, indices in clusters.items():
                if len(indices) > 1 or cluster_name.startswith("noise_"):
                    filtered_clusters[cluster_name] = indices

            logger.info(f"HDBSCAN found {len(filtered_clusters)} clusters for {len(embeddings)} texts")
            return filtered_clusters

        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return self._cluster_similarity_threshold(embeddings)

    def _cluster_kmeans(self, embeddings: np.ndarray, n_clusters: Optional[int] = None) -> Dict[str, List[int]]:
        """Cluster using k-means."""
        try:
            if n_clusters is None:
                # Estimate number of clusters based on dataset size
                n_clusters = max(2, min(10, len(embeddings) // 10))

            logger.info(f"Clustering with k-means ({n_clusters} clusters)")

            kmeans = self.sklearn['KMeans'](
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )

            cluster_labels = kmeans.fit_predict(embeddings)

            # Group by cluster labels
            clusters = {}
            for i, label in enumerate(cluster_labels):
                cluster_name = f"cluster_{label}"
                if cluster_name not in clusters:
                    clusters[cluster_name] = []
                clusters[cluster_name].append(i)

            logger.info(f"k-means found {len(clusters)} clusters for {len(embeddings)} texts")
            return clusters

        except Exception as e:
            logger.error(f"k-means clustering failed: {e}")
            return self._cluster_similarity_threshold(embeddings)

    def _cluster_similarity_threshold(self, embeddings: np.ndarray, threshold: float = 0.7) -> Dict[str, List[int]]:
        """Simple similarity-based clustering as ultimate fallback."""
        logger.info("Using similarity threshold clustering (fallback)")

        clusters = {}
        cluster_id = 0

        for i, embedding in enumerate(embeddings):
            assigned = False
            for cluster_name, indices in clusters.items():
                # Check similarity with cluster centroid
                if indices:
                    centroid = np.mean(embeddings[indices], axis=0)
                    similarity = np.dot(embedding, centroid) / (np.linalg.norm(embedding) * np.linalg.norm(centroid))
                    if similarity > threshold:
                        clusters[cluster_name].append(i)
                        assigned = True
                        break

            if not assigned:
                clusters[f"cluster_{cluster_id}"] = [i]
                cluster_id += 1

        # Remove clusters with only one item
        filtered_clusters = {k: v for k, v in clusters.items() if len(v) > 1}

        logger.info(f"Similarity clustering found {len(filtered_clusters)} clusters for {len(embeddings)} texts")
        return filtered_clusters

    def extract_keywords(self, texts: List[str], max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from a collection of texts using YAKE or n-gram fallback.

        Args:
            texts: List of texts to extract keywords from
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keywords sorted by relevance
        """
        if not texts:
            return []

        combined_text = " ".join(texts)

        if self.yake_available:
            return self._extract_keywords_yake(combined_text, max_keywords)
        elif self.nltk_available and self.sklearn_available:
            return self._extract_keywords_ngrams(combined_text, max_keywords)
        else:
            return self._extract_keywords_simple(combined_text, max_keywords)

    def _extract_keywords_yake(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using YAKE."""
        try:
            # Configure YAKE keyword extractor
            kw_extractor = self.yake.KeywordExtractor(
                lan="en",
                n=2,  # n-gram size (1 for unigrams, 2 for bigrams, etc.)
                dedupLim=0.9,  # deduplication threshold
                windowsSize=2,  # context window size
                top=max_keywords * 2  # Extract more candidates
            )

            # Extract keywords
            keywords = kw_extractor.extract_keywords(text)

            # Return just the keyword strings (YAKE returns tuples of (keyword, score))
            result = [kw[0] for kw in keywords[:max_keywords]]

            logger.debug(f"YAKE extracted {len(result)} keywords")
            return result

        except Exception as e:
            logger.warning(f"YAKE keyword extraction failed: {e}")
            return self._extract_keywords_ngrams(text, max_keywords)

    def _extract_keywords_ngrams(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using TF-IDF and n-grams."""
        try:
            # Preprocess text
            text = self._preprocess_text(text)

            # Create TF-IDF vectorizer for n-grams
            vectorizer = self.sklearn['TfidfVectorizer'](
                ngram_range=(1, 3),  # unigrams, bigrams, trigrams
                max_features=1000,
                stop_words='english',
                min_df=1
            )

            # Fit and transform (single document)
            tfidf_matrix = vectorizer.fit_transform([text])

            # Get feature names and scores
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # Sort by TF-IDF score and filter
            keyword_candidates = [
                (feature_names[i], scores[i])
                for i in range(len(feature_names))
                if scores[i] > 0
            ]
            keyword_candidates.sort(key=lambda x: x[1], reverse=True)

            # Extract keywords, preferring longer n-grams
            keywords = []
            seen_words = set()

            for keyword, score in keyword_candidates:
                # Avoid duplicates and very short keywords
                words = keyword.split()
                if len(words) >= 1 and not any(word in seen_words for word in words):
                    keywords.append(keyword)
                    seen_words.update(words)

                if len(keywords) >= max_keywords:
                    break

            logger.debug(f"n-gram TF-IDF extracted {len(keywords)} keywords")
            return keywords[:max_keywords]

        except Exception as e:
            logger.warning(f"n-gram keyword extraction failed: {e}")
            return self._extract_keywords_simple(text, max_keywords)

    def _extract_keywords_simple(self, text: str, max_keywords: int) -> List[str]:
        """Simple keyword extraction using frequency analysis."""
        try:
            # Preprocess text
            text = self._preprocess_text(text)

            # Simple tokenization and counting
            words = re.findall(r'\b\w+\b', text.lower())
            word_counts = Counter(words)

            # Remove stopwords if available
            if self.nltk_available:
                stop_words = set(self.nltk['stopwords'].words('english'))
                word_counts = Counter({
                    word: count for word, count in word_counts.items()
                    if word not in stop_words and len(word) > 2
                })

            # Get most common words
            keywords = [word for word, _ in word_counts.most_common(max_keywords)]

            logger.debug(f"Simple frequency extracted {len(keywords)} keywords")
            return keywords

        except Exception as e:
            logger.error(f"Simple keyword extraction failed: {e}")
            return []

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword extraction."""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs, emails, mentions (reuse from text processing)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'@\w+', '', text)

        # Remove punctuation and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def get_similar_texts(self, query: str, n_results: int = 5) -> List[Dict]:
        """Find similar texts to a query"""
        # Generate query embedding
        query_embeddings = self.embedding_service.generate_embeddings([query])
        if query_embeddings is None:
            return []

        query_embedding = query_embeddings[0]

        # Search using embedding service
        results = self.embedding_service.search_similar(query_embedding, n_results=n_results)

        return results

    def cluster_texts_with_keywords(
        self,
        texts: List[str],
        n_clusters: Optional[int] = None,
        use_umap: bool = True,
        max_keywords_per_cluster: int = 10
    ) -> Dict[str, Dict[str, Any]]:
        """
        Cluster texts and extract keywords for each cluster.

        Args:
            texts: List of texts to cluster
            n_clusters: Target number of clusters
            use_umap: Whether to use UMAP
            max_keywords_per_cluster: Maximum keywords per cluster

        Returns:
            Dict mapping cluster names to cluster info with keywords
        """
        clusters, embeddings, reduced_embeddings = self.cluster_texts(
            texts, n_clusters, use_umap
        )

        # Extract keywords for each cluster
        cluster_info = {}
        for cluster_name, indices in clusters.items():
            cluster_texts = [texts[i] for i in indices]

            # Extract keywords for this cluster
            keywords = self.extract_keywords(cluster_texts, max_keywords_per_cluster)

            # Generate cluster label from top keywords
            cluster_label = self._generate_cluster_label(keywords, cluster_texts)

            cluster_info[cluster_name] = {
                "indices": indices,
                "size": len(indices),
                "keywords": keywords,
                "label": cluster_label,
                "texts": cluster_texts
            }

        return cluster_info

    def _generate_cluster_label(self, keywords: List[str], texts: List[str]) -> str:
        """Generate a human-readable label for a cluster."""
        if not keywords:
            return "Miscellaneous"

        # Use first 1-3 keywords as label
        if len(keywords) >= 3:
            label = f"{keywords[0]}, {keywords[1]}, {keywords[2]}"
        elif len(keywords) >= 2:
            label = f"{keywords[0]}, {keywords[1]}"
        else:
            label = keywords[0]

        # Capitalize first letter
        return label.capitalize()
