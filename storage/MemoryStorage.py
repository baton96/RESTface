from .BaseStorage import BaseStorage


class MemoryStorage(BaseStorage):
    def __init__(self, uuid_id: bool = False):
        super().__init__(None, uuid_id)
        self.db = {}

    def get_with_id(self, collection_name: str, item_id: int | str) -> dict:
        collection = self.db.get(collection_name, {})
        return collection.get(item_id, {})

    def put_n_post(
        self, collection_name: str, data: dict, method: str = "POST"
    ) -> int | str:
        collection = self.db.setdefault(collection_name, {})
        item_id = self.get_id(collection_name, data)
        if method == "POST":
            collection.setdefault(item_id, {}).update(data)
        elif method == "PUT":
            collection[item_id] = data
        return item_id

    def bulk_put_n_post(
        self, collection_name: str, items: list[dict], method: str = "POST"
    ) -> list[int | str]:
        return [self.put_n_post(collection_name, item, method) for item in items]

    def delete(
        self, collection_name: str, where_params: list, item_id: int | str = None
    ) -> None:
        if not item_id:
            self.db.pop(collection_name, None)
        else:
            collection = self.db.setdefault(collection_name, {})
            for item in list(collection.values()):
                if all(self.fulfill_cond(item, param) for param in where_params):
                    collection.pop(item["id"], None)

    def all(self) -> dict:
        return {
            collection_name: list(items.values())
            for collection_name, items in self.db.items()
        }

    def reset(self) -> None:
        self.db = {}

    def get_ids(self, collection_name: str) -> set:
        collection = self.db.setdefault(collection_name, {})
        return set(collection.keys())

    def get_items(self, collection_name: str) -> list[dict]:
        collection = self.db.setdefault(collection_name, {})
        return list(collection.values())
