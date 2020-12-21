import json
from redis import Redis
from app.core import date_object_converter


class QueueManager:
    __QUEUE_NAME = 'call_request_queue'
    __QUEUE_TIME = 3600

    def __init__(self, redis: Redis):
        self.__redis = redis

    def queue_call(self, call_details: dict):
        self.__redis.expire(self.__QUEUE_NAME, 3600)
        self.__redis.rpush(
            self.__QUEUE_NAME,
            json.dumps(call_details, default=date_object_converter)
        )

    def get_number_of_queued_calls(self):
        return int(self.__redis.llen(self.__QUEUE_NAME))

    def get_next_call_in_queue(self):
        if self.is_empty():
            return None
        raw_data = self.__redis.lpop(self.__QUEUE_NAME)
        return dict(json.loads(raw_data))

    def is_empty(self):
        return int(self.__redis.llen(self.__QUEUE_NAME)) == 0

    def clear(self):
        self.__redis.delete(self.__QUEUE_NAME)
