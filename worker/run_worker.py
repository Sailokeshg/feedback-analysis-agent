#!/usr/bin/env python3
"""RQ Worker entry point for processing customer feedback"""

import os
import redis
from rq import Worker, Queue, Connection

# Listen on all queues by default
listen = ['default', 'feedback_processing']

# Set up Redis connection
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

if __name__ == '__main__':
    with Connection(redis.from_url(redis_url)):
        worker = Worker(map(Queue, listen))
        worker.work()
