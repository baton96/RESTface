import itertools
import operator
import re
from typing import Optional
import dataset

root = {}
db = {}


class MemoryStorage:
    def __init__(self):
        op_names = ['eq', 'ge', 'gt', 'le', 'lt', 'ne']
        self.ops = {
            op_name: getattr(operator, op_name)
            for op_name in op_names
        }
        self.ops.update({
            'between': lambda item, collection: collection[0] <= item <= collection[-1],
            'ilike': lambda string, pattern: re.search(pattern, str(string).lower()),
            'like': lambda string, pattern: re.search(pattern, str(string)),
            'startswith': lambda string, pattern: str(string).startswith(pattern),
            'endswith': lambda string, pattern: str(string).endswith(pattern),
            'notin': lambda item, collection: str(item) not in collection,
            'in': lambda item, collection: str(item) in collection,
            'gte': operator.ge,
            'lte': operator.le,
            'neq': operator.ne,
            'not': operator.ne,
            '=': operator.eq,
        })

    def create_if_not_exists(self, collection_name: str):
        if collection_name not in root:
            root[collection_name] = {}

    def get_with_id(self, collection_name: str, item_id: int):
        collection = root.get(collection_name, {})
        return collection.get(item_id, {})

    def get_without_id(self, collection_name: str, where_params: list, meta_params: dict):
        items = list(root.get(collection_name, {}).values())
        items = [
            item for item in items if all(
                self.fulfill_cond(item, param)
                for param in where_params
            )
        ]

        # Sorting, keep None-s and put them on the beginning of results
        order_by = meta_params['order_by']
        order_key = lambda item: ((value := item.get(order_by)) is not None, value, item['id'])

        desc = meta_params['desc']
        items = sorted(items, key=order_key, reverse=desc)

        offset = meta_params['_offset']
        limit = meta_params['_limit'] or len(items) - offset
        return items[offset: offset + limit]

    def post(self, collection_name: str, data: Optional[dict] = None):
        data = data or {}
        collection = root[collection_name]
        item_id = data.get('id') or self.generate_id(collection_name)
        collection.setdefault(item_id, {}).update({'id': item_id, **data})
        return item_id

    def put(self, collection_name: str, data: Optional[dict] = None):
        data = data or {}
        collection = root[collection_name]
        item_id = data.get('id') or self.generate_id(collection_name)
        collection[item_id] = {'id': item_id, **data}
        return item_id

    def delete(self, collection_name: str, item_id: Optional[int] = None) -> bool:
        if item_id:
            collection = root[collection_name]
            return bool(collection.pop(item_id, None))
        else:
            return bool(root.pop(collection_name, None))

    def generate_id(self, collection_name: str):
        ids = root[collection_name].keys()
        for i in itertools.count(1):
            if i not in ids:
                return i

    def fulfill_cond(self, item, parsed_param):
        op_name, param_name, param_value = parsed_param
        if param_value:
            op = self.ops[op_name]
        else:
            op = lambda field, _: field is not None
        return op(item.get(param_name), param_value)


class DbStorage:
    def __init__(self):
        global db
        db = dataset.connect('sqlite:///:memory:', row_type=dict)

    def create_if_not_exists(self, table_name: str):
        _ = db[table_name].table

    def get_with_id(self, table_name: str, item_id: int):
        return db[table_name].find_one(id=item_id) or {}

    def get_without_id(self, table_name: str, where_params: list, meta_params: dict):
        where_params = {
            param_name: (
                {op_name: param_value} if param_value else {'not': None}
            )
            for op_name, param_name, param_value in where_params
        }
        if meta_params.pop('desc', False):
            meta_params['order_by'] = '-' + meta_params['order_by']
        if not meta_params['_limit']:
            meta_params.pop('_limit', None)
        params = {**where_params, **meta_params}
        items = list(db[table_name].find(**params))
        return items

    def post(self, table_name: str, data: Optional[dict] = None):
        data = data or {}
        # existing -> True, nonexisting -> id
        return db[table_name].upsert(data, ['id'])

    def put(self, table_name: str, data: Optional[dict] = None):
        data = data or {}
        item_id = data.get('id')
        db[table_name].delete(id=item_id)
        # existing -> True, nonexisting -> id
        return db[table_name].insert(data)

    def delete(self, table_name: str, item_id: Optional[int] = None) -> bool:
        if item_id:
            existed = db[table_name].delete(id=item_id)
            return existed
        else:
            existed = table_name in db.tables
            db[table_name].drop()
            return existed
