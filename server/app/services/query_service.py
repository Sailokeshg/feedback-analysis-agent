from .clustering_service import ClusteringService
from .sentiment_service import SentimentService
from ..models.feedback import FeedbackItem
from .database import SessionLocal
from typing import Dict, List

class QueryService:
    def __init__(self):
        self.clustering_service = ClusteringService()
        self.sentiment_service = SentimentService()

    async def process_query(self, query: str) -> Dict:
        """Process a natural language query and return answer with sources"""

        # Simple rule-based query processing (can be enhanced with LLM)
        query_lower = query.lower()

        db = SessionLocal()
        try:
            base_query = db.query(FeedbackItem)

            # Parse query intent
            if "positive" in query_lower:
                results = base_query.filter(FeedbackItem.sentiment == "positive").limit(10).all()
                answer = f"Found {len(results)} positive feedback items"
            elif "negative" in query_lower:
                results = base_query.filter(FeedbackItem.sentiment == "negative").limit(10).all()
                answer = f"Found {len(results)} negative feedback items"
            elif "neutral" in query_lower:
                results = base_query.filter(FeedbackItem.sentiment == "neutral").limit(10).all()
                answer = f"Found {len(results)} neutral feedback items"
            elif "topic" in query_lower or "cluster" in query_lower:
                # Get topic distribution
                topics = {}
                all_feedback = base_query.all()
                for item in all_feedback:
                    topics[item.topic_cluster] = topics.get(item.topic_cluster, 0) + 1

                top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
                answer = f"Top topics: {', '.join([f'{topic} ({count})' for topic, count in top_topics])}"
                results = all_feedback[:10]  # Return sample
            else:
                # Default: find similar items using vector search
                similar_texts = self.clustering_service.get_similar_texts(query, 5)
                results = []
                for item in similar_texts:
                    # Find matching feedback items
                    feedback = base_query.filter(FeedbackItem.text.contains(item['text'][:100])).first()
                    if feedback:
                        results.append(feedback)

                answer = f"Found {len(results)} relevant feedback items similar to your query"

            # Format sources
            sources = [
                {
                    "id": str(item.id),
                    "text": item.text,
                    "sentiment": item.sentiment,
                    "topic_cluster": item.topic_cluster,
                    "created_at": item.created_at.isoformat(),
                }
                for item in results
            ]

            return {
                "answer": answer,
                "sources": sources
            }

        finally:
            db.close()
