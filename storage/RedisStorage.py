import json
import redis

from .BaseStorage import BaseStorage


class RedisStorage(BaseStorage):
    def __init__(self, _: str | None = None, uuid_id: bool = False):
        super().__init__()
        self.db = redis.Redis(decode_responses=True)
        self.primary_type = str if uuid_id else int

    def get_with_id(self, collection_name: str, item_id: int | str) -> dict:
        item = {
            k: self.decode(v)
            for k, v in (self.db.hgetall(f"{collection_name}:{item_id}") or {}).items()  # type: ignore[union-attr]
        }
        return item

    def upsert(
        self, collection_name: str, data: dict, method: str = "POST"
    ) -> int | str:
        item_id = self.get_id(collection_name, data)
        if method == "PUT":
            self.db.delete(f"{collection_name}:{item_id}")
        data = {k: self.encode(v) for k, v in data.items()}
        self.db.hset(f"{collection_name}:{item_id}", mapping=data)
        self.db.sadd("collections", collection_name)
        self.db.sadd(collection_name, item_id)
        return item_id

    def bulk_upsert(
        self, collection_name: str, items: list[dict], method: str = "POST"
    ) -> list[int | str]:
        self.bulk_get_ids(collection_name, items)
        if method == "PUT":
            for item in items:
                self.db.delete(f"{collection_name}:{item['id']}")
        for item in items:
            item = {k: self.encode(v) for k, v in item.items()}
            self.db.hset(f"{collection_name}:{item['id']}", mapping=item)
            self.db.sadd(collection_name, item["id"])
        self.db.sadd("collections", collection_name)
        return [item["id"] for item in items]

    def delete_with_id(self, collection_name: str, doc_id: int | str) -> bool:
        return bool(
            self.db.delete(f"{collection_name}:{doc_id}")
            and self.db.srem(collection_name, doc_id)
        )

    def delete_without_id(self, collection_name: str, where_params: list) -> None:
        if where_params:
            item_ids = [
                item["id"]
                for item in self.get_items(collection_name)
                if all(self.fulfill_cond(item, param) for param in where_params)
            ]
            if item_ids:
                self.db.delete(
                    *(f"{collection_name}:{item_id}" for item_id in item_ids)
                )
                self.db.srem(collection_name, *item_ids)
        else:
            members = self.db.smembers(collection_name)
            if members:
                self.db.delete(
                    *(f"{collection_name}:{item_id}" for item_id in members)  # type: ignore[union-attr]
                )
                self.db.srem("collections", collection_name)
                self.db.delete(collection_name)

    def all(self):
        items = {
            collection_name: sorted(
                [
                    {
                        k: self.decode(v)
                        for k, v in self.db.hgetall(
                            f"{collection_name}:{item_id}"
                        ).items()
                    }
                    for item_id in self.db.smembers(collection_name)
                ],
                key=lambda item: item["id"],
            )
            for collection_name in self.db.smembers("collections")
        }
        return items

    def reset(self) -> None:
        self.db.flushdb()

    def get_ids(self, collection_name: str) -> list[int | str]:
        item_ids = [
            int(item_id) if item_id.isdigit() else item_id
            for item_id in self.db.smembers(collection_name)  # type: ignore[union-attr]
        ]
        return item_ids

    def get_items(self, collection_name) -> list[dict]:
        items = [
            self.get_with_id(collection_name, item_id)
            for item_id in self.db.smembers(collection_name)  # type: ignore[union-attr]
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
