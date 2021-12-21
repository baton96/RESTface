import operator
import re

import tinydb

from .BaseStorage import BaseStorage

db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)


class FileStorage(BaseStorage):
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

    def get_with_id(self, table_name: str, item_id: int) -> dict:
        table = db.table(table_name)
        return table.get(doc_id=item_id) or {}

    def get_without_id(self, table_name: str, where_params: list, meta_params: dict):
        table = db.table(table_name)
        items = [
            item for item in table.all() if all(
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

    def post(self, table_name: str, data: dict):
        table = db.table(table_name)
        doc_id = data.get('id')
        if doc_id:
            return table.upsert(tinydb.table.Document(data, doc_id=doc_id))[0]
        else:
            doc_id = table.insert(data)
            table.update({'id': doc_id}, doc_ids=[doc_id])
            return doc_id

    def put(self, table_name: str, data: dict):
        table = db.table(table_name)
        doc_id = data.get('id')
        if doc_id:
            table.remove(doc_ids=[doc_id])
            return table.upsert(tinydb.table.Document(data, doc_id=doc_id))[0]
        else:
            return table.insert(data)

    def delete(self, table_name: str, item_id: int = None) -> bool:
        if item_id:
            table = db.table(table_name)
            try:
                table.remove(doc_ids=[item_id])
                return True
            except KeyError:
                return False
        else:
            existed = table_name in db.tables()
            db.drop_table(table_name)
            return existed

    def fulfill_cond(self, item, parsed_param):
        op_name, param_name, param_value = parsed_param
        if param_value:
            op = self.ops[op_name]
        else:
            op = lambda field, _: field is not None
        return op(item.get(param_name), param_value)
