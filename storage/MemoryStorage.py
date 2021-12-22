import itertools
import operator
import re
import uuid

from .JSONStorage import JSONStorage


class MemoryStorage(JSONStorage):
    def __init__(self, uuid_id: bool = False):
        super().__init__(None, uuid_id)
        self.root = {}

    def get_with_id(self, collection_name: str, item_id: int):
        collection = self.root.get(collection_name, {})
        return collection.get(item_id, {})

    def get_without_id(self, collection_name: str, where_params: list, meta_params: dict):
        items = list(self.root.get(collection_name, {}).values())
        items = [
            item for item in items if all(
                self.fulfill_cond(item, param)
                for param in where_params
            )
        ]

        # Sorting, keep None-s and put them on the beginning of results
        order_by = meta_params['order_by']
        order_key = lambda item: tuple(
            [
                ((value := item.get(order_by_arg.lstrip('-'))) is not None, value)
                for order_by_arg in order_by
            ] + [item['id']]
        )

        desc = meta_params['desc']
        items = sorted(items, key=order_key, reverse=desc)

        offset = meta_params['_offset']
        limit = meta_params['_limit'] or len(items) - offset
        return items[offset: offset + limit]

    def post(self, collection_name: str, data: dict):
        collection = self.root.setdefault(collection_name, {})
        item_id = data.get('id')
        if not item_id:
            item_ids = self.root.setdefault(collection_name, {}).keys()
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

    def put(self, collection_name: str, data: dict):
        collection = self.root.setdefault(collection_name, {})
        item_id = data.get('id') or self.generate_id(collection_name)
        collection[item_id] = {'id': item_id, **data}
        return item_id

    def delete(self, collection_name: str, item_id: int = None) -> bool:
        if item_id:
            collection = self.root.setdefault(collection_name, {})
            return bool(collection.pop(item_id, None))
        else:
            return bool(self.root.pop(collection_name, None))

    def all(self):
        return self.root

    def reset(self):
        self.root = {}
