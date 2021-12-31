import json
from typing import Union, List

import redis

from .BaseStorage import BaseStorage


class RedisStorage(BaseStorage):
    def __init__(self, _: str = None, uuid_id: bool = False):
        super().__init__()
        self.db = redis.Redis(decode_responses=True)
        self.primary_type = str if uuid_id else int

    def get_with_id(self, collection_name: str, item_id: Union[int, str]) -> dict:
        item = {
            k: self.decode(v)
            for k, v in (self.db.hgetall(f'{collection_name}:{item_id}') or {}).items()
        }
        return item

    def put_n_post(self, collection_name: str, data: dict, method: str = 'POST') -> Union[int, str]:
        item_id = self.get_id(collection_name, data)
        if method == 'PUT':
            self.db.delete(f'{collection_name}:{item_id}')
        data = {k: self.encode(v) for k, v in data.items()}
        self.db.hset(f'{collection_name}:{item_id}', mapping=data)
        self.db.sadd('collections', collection_name)
        self.db.sadd(collection_name, item_id)
        return item_id

    def delete(self, collection_name: str, item_id: Union[int, str] = None):
        if item_id:
            self.db.delete(f'{collection_name}:{item_id}')
            self.db.srem(collection_name, item_id)
        else:
            item_ids = self.db.smembers(collection_name)
            for item_id in item_ids:
                self.db.delete(f'{collection_name}:{item_id}')
            self.db.srem('collections', collection_name)
            self.db.delete(collection_name)

    def all(self):
        items = {
            collection_name: sorted([
                {
                    k: self.decode(v)
                    for k, v in self.db.hgetall(f'{collection_name}:{item_id}').items()
                } for item_id in self.db.smembers(collection_name)
            ], key=lambda item: item['id'])
            for collection_name in self.db.smembers('collections')
        }
        return items

    def reset(self) -> None:
        self.db.flushdb()

    def get_ids(self, collection_name: str) -> set:
        item_ids = {
            int(item_id) if item_id.isdigit() else item_id
            for item_id in self.db.smembers(collection_name)
        }
        return item_ids

    def get_items(self, collection_name) -> List[dict]:
        items = [
            self.get_with_id(collection_name, item_id)
            for item_id in self.db.smembers(collection_name)
        ]
        return items

    def decode(self, obj):
        try:
            return json.loads(obj)
        except ValueError:
            return obj

    def encode(self, obj):
        try:
            return json.dumps(obj)
        except ValueError:
            return obj
