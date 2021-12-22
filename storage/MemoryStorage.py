import itertools
import uuid

from .JSONStorage import JSONStorage


class MemoryStorage(JSONStorage):
    def __init__(self, uuid_id: bool = False):
        super().__init__(None, uuid_id)
        self.db = {}

    def get_with_id(self, collection_name: str, item_id: int):
        collection = self.db.get(collection_name, {})
        return collection.get(item_id, {})

    def post(self, collection_name: str, data: dict):
        collection = self.db.setdefault(collection_name, {})
        item_id = data.get('id')
        if not item_id:
            item_ids = self.db.setdefault(collection_name, {}).keys()
            if self.primary_type == int:
                item_id = max(item_ids or {0}) + 1
            elif self.primary_type == str:
                generator = (str(uuid.uuid4()) for _ in itertools.count())
                for item_id in generator:
                    if item_id not in item_ids:
                        break
            data['id'] = item_id
        collection.setdefault(item_id, {}).update({'id': item_id, **data})
        return item_id

    def delete(self, collection_name: str, item_id: int = None) -> bool:
        if item_id:
            collection = self.db.setdefault(collection_name, {})
            return bool(collection.pop(item_id, None))
        else:
            return bool(self.db.pop(collection_name, None))

    def all(self):
        return self.db

    def reset(self):
        self.db = {}

    def get_items(self, collection_name: str):
        return list(self.db.get(collection_name, {}).values())
