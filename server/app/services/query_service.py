from .clustering_service import ClusteringService
from .sentiment_service import SentimentService
from ..models.feedback import Feedback, NLPAnnotation
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
            # Join Feedback with NLPAnnotation to get sentiment info
            base_query = db.query(Feedback).join(NLPAnnotation, Feedback.id == NLPAnnotation.feedback_id)

            # Parse query intent
            if "positive" in query_lower:
                results = base_query.filter(NLPAnnotation.sentiment == 1).limit(10).all()
                answer = f"Found {len(results)} positive feedback items"
            elif "negative" in query_lower:
                results = base_query.filter(NLPAnnotation.sentiment == -1).limit(10).all()
                answer = f"Found {len(results)} negative feedback items"
            elif "neutral" in query_lower:
                results = base_query.filter(NLPAnnotation.sentiment == 0).limit(10).all()
                answer = f"Found {len(results)} neutral feedback items"
            elif "topic" in query_lower or "cluster" in query_lower:
                # Get topic distribution by joining with annotations
                from ..models.feedback import Topic
                topic_query = db.query(Topic.label, db.func.count(NLPAnnotation.id)).\
                    join(NLPAnnotation, Topic.id == NLPAnnotation.topic_id).\
                    group_by(Topic.id, Topic.label).\
                    order_by(db.func.count(NLPAnnotation.id).desc()).\
                    limit(5).all()

                top_topics = [(label, count) for label, count in topic_query]
                answer = f"Top topics: {', '.join([f'{topic} ({count})' for topic, count in top_topics])}"
                results = base_query.limit(10).all()  # Return sample
            else:
                # Default: find similar items using vector search
                similar_texts = self.clustering_service.get_similar_texts(query, 5)
                results = []
                for item in similar_texts:
                    # Find matching feedback items
                    feedback = base_query.filter(Feedback.text.contains(item['text'][:100])).first()
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
