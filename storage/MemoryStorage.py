from typing import List, Union

from .JSONStorage import JSONStorage


class MemoryStorage(JSONStorage):
    def __init__(self, uuid_id: bool = False):
        super().__init__(None, uuid_id)
        self.db = {}

    def get_with_id(self, collection_name: str, item_id: Union[int, str]) -> dict:
        collection = self.db.get(collection_name, {})
        return collection.get(item_id, {})

    def post(self, collection_name: str, data: List[dict]):
        collection = self.get_table(collection_name)
        item_ids = []
        for item in data:
            item_id = self.get_id(collection_name, item)
            item_ids.append(item_id)
            collection.setdefault(item_id, {}).update({'id': item_id, **item})
        return item_ids

    def delete(self, collection_name: str, item_id: Union[int, str] = None) -> bool:
        if item_id:
            collection = self.db.setdefault(collection_name, {})
            return bool(collection.pop(item_id, None))
        else:
            return bool(self.db.pop(collection_name, None))

    def all(self):
        return self.db

    def reset(self) -> None:
        self.db = {}

    def get_table(self, collection_name: str):
        return self.db.setdefault(collection_name, {})

    def get_items(self, collection_name: str):
        return list(self.get_table(collection_name).values())
