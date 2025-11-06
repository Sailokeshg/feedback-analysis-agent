from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict

class ClusteringService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="feedback_embeddings")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        return self.model.encode(texts, convert_to_numpy=True)

    def cluster_texts(self, texts: List[str], n_clusters: int = None) -> Dict[str, List[int]]:
        """Cluster texts using embeddings and return cluster assignments"""
        if len(texts) < 2:
            return {"cluster_0": list(range(len(texts)))}

        embeddings = self.generate_embeddings(texts)

        # Store in Chroma for later retrieval
        ids = [f"doc_{i}" for i in range(len(texts))]
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            ids=ids
        )

        # Simple clustering based on similarity (can be improved with proper clustering)
        # For MVP, we'll use a simple threshold-based clustering
        clusters = {}
        cluster_id = 0

        for i, embedding in enumerate(embeddings):
            assigned = False
            for cluster_name, indices in clusters.items():
                # Check similarity with cluster centroid
                if indices:
                    centroid = np.mean(embeddings[indices], axis=0)
                    similarity = np.dot(embedding, centroid) / (np.linalg.norm(embedding) * np.linalg.norm(centroid))
                    if similarity > 0.7:  # Similarity threshold
                        clusters[cluster_name].append(i)
                        assigned = True
                        break

            if not assigned:
                clusters[f"cluster_{cluster_id}"] = [i]
                cluster_id += 1

        return clusters

    def get_similar_texts(self, query: str, n_results: int = 5) -> List[Dict]:
        """Find similar texts to a query"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        return [
            {
                "text": doc,
                "distance": dist
            }
            for doc, dist in zip(results['documents'][0], results['distances'][0])
        ]
