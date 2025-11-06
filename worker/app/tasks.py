import os
import sys
import uuid
from datetime import datetime

# Add server path to sys.path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../server'))

from app.models.feedback import FeedbackItem
from app.services.database import SessionLocal, create_tables
from app.services.sentiment_service import SentimentService
from app.services.clustering_service import ClusteringService

def process_feedback_batch(feedback_data: list):
    """Process a batch of feedback items: analyze sentiment and cluster topics"""

    # Initialize services
    sentiment_service = SentimentService()
    clustering_service = ClusteringService()

    # Create tables if they don't exist
    create_tables()

    db = SessionLocal()
    try:
        # Extract texts for batch processing
        texts = [item['text'] for item in feedback_data]

        # Analyze sentiment in batch
        print(f"Analyzing sentiment for {len(texts)} items...")
        sentiment_results = sentiment_service.analyze_batch(texts)

        # Assign sentiment to feedback data
        for i, (sentiment, score) in enumerate(sentiment_results):
            feedback_data[i]['sentiment'] = sentiment
            feedback_data[i]['sentiment_score'] = score

        # Cluster topics
        print("Clustering topics...")
        cluster_assignments = clustering_service.cluster_texts(texts)

        # Assign cluster labels
        for cluster_name, indices in cluster_assignments.items():
            for idx in indices:
                feedback_data[idx]['topic_cluster'] = cluster_name

        # Save to database
        print(f"Saving {len(feedback_data)} items to database...")
        for item in feedback_data:
            feedback_item = FeedbackItem(
                id=item.get('id', str(uuid.uuid4())),
                text=item['text'],
                sentiment=item['sentiment'],
                sentiment_score=item['sentiment_score'],
                topic_cluster=item['topic_cluster'],
                source=item.get('source', 'api'),
                created_at=item.get('created_at', datetime.utcnow())
            )
            db.add(feedback_item)

        db.commit()
        print(f"Successfully processed {len(feedback_data)} feedback items")

        return {
            "processed_count": len(feedback_data),
            "status": "completed"
        }

    except Exception as e:
        db.rollback()
        print(f"Error processing feedback batch: {str(e)}")
        raise e
    finally:
        db.close()
