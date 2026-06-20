import os

PROCESSING_SECONDS = float(os.getenv("PROCESSING_SECONDS", "3"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "1000"))
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))

STREAM_KEY = "jobs"
CONSUMER_GROUP = "jobs:group"
CONSUMER_NAME = "worker1"
