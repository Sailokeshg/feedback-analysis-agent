import pandas as pd
import uuid
from datetime import datetime
from ..models.feedback import Feedback
from .database import SessionLocal
from .sentiment_service import SentimentService
from .clustering_service import ClusteringService
import redis
import rq

class UploadService:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.clustering_service = ClusteringService()
        self.redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        self.queue = rq.Queue('feedback_processing', connection=self.redis_conn)

    async def process_upload(self, file):
        """Process uploaded CSV file containing customer feedback"""
        try:
            # Read CSV
            df = pd.read_csv(file.file)

            # Validate required columns
            required_columns = ['text']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV must contain columns: {required_columns}")

            # Add metadata
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df['created_at'] = datetime.utcnow()
            df['source'] = 'csv_upload'

            # Queue processing job
            job = self.queue.enqueue(
                'worker.tasks.process_feedback_batch',
                df.to_dict('records')
            )

            return {
                "job_id": job.id,
                "processed_count": len(df),
                "status": "queued"
            }

        except Exception as e:
            raise Exception(f"Failed to process upload: {str(e)}")
