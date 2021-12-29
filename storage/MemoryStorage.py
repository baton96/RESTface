from typing import Union, List

from .JSONStorage import JSONStorage


class MemoryStorage(JSONStorage):
    def __init__(self, uuid_id: bool = False):
        super().__init__(None, uuid_id)
        self.db = {}

    def get_with_id(self, collection_name: str, item_id: Union[int, str]) -> dict:
        collection = self.db.get(collection_name, {})
        return collection.get(item_id, {})

    def put_n_post(self, collection_name: str, data: dict, method: str = 'POST') -> Union[int, str]:
        collection = self.get_table(collection_name)
        item_id = self.get_id(collection_name, data)
        if method == 'POST':
            collection.setdefault(item_id, {}).update(data)
        elif method == 'PUT':
            collection[item_id] = data
        return item_id

    def delete(self, collection_name: str, item_id: Union[int, str] = None) -> bool:
        if item_id:
            collection = self.db.setdefault(collection_name, {})
            return bool(collection.pop(item_id, None))
        else:
            return bool(self.db.pop(collection_name, None))

    def all(self) -> dict:
        return {
            collection_name: list(items.values())
            for collection_name, items in self.db.items()
        }

    def reset(self) -> None:
        self.db = {}

    def get_table(self, collection_name: str):
        return self.db.setdefault(collection_name, {})

    def get_items(self, collection_name: str) -> List[dict]:
        return list(self.get_table(collection_name).values())
