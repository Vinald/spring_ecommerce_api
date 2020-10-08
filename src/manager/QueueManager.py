import json
from redis import Redis
from src.utils import date_object_converter


class QueueManager:
    QUEUE_NAME = 'call_request_queue'
    QUEUE_TIME = 3600

    def __init__(self, redis: Redis):
        self.redis = redis

    def queue_call(self, call_details: dict):
        self.redis.expire(self.QUEUE_NAME, 3600)
        self.redis.rpush(self.QUEUE_NAME, json.dumps(call_details, default=date_object_converter))

    def get_number_of_queued_calls(self):
        return int(self.redis.llen(self.QUEUE_NAME))

    def get_next_call_in_queue(self):
        if self.is_empty():
            return None
        raw_data = self.redis.lpop(self.QUEUE_NAME)
        return dict(json.loads(raw_data))

    def is_empty(self):
        return int(self.redis.llen(self.QUEUE_NAME)) == 0

    def clear(self):
        self.redis.delete(self.QUEUE_NAME)
