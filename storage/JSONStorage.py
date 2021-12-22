import itertools
import operator
import re
import uuid
from abc import ABC, abstractmethod

from .BaseStorage import BaseStorage


class JSONStorage(BaseStorage, ABC):
    def __init__(self, _: str = None, uuid_id: bool = False):
        self.primary_type = str if uuid_id else int

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

    def fulfill_cond(self, item, parsed_param):
        op_name, param_name, param_value = parsed_param
        if param_value:
            op = self.ops[op_name]
        else:
            op = lambda field, _: field is not None
        return op(item.get(param_name), param_value)

    @abstractmethod
    def get_table(self, collection_name: str):
        pass

    @abstractmethod
    def get_items(self, collection_name):
        pass

    def get_without_id(self, collection_name: str, where_params: list, meta_params: dict):
        items = self.get_items(collection_name)
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

    def get_id(self, collection_name: str, data: dict):
        item_id = data.get('id')
        if not item_id:
            item_ids = {item['id'] for item in self.get_items(collection_name)}
            if self.primary_type == int:
                item_id = max(item_ids or {0}) + 1
            elif self.primary_type == str:
                generator = (str(uuid.uuid4()) for _ in itertools.count())
                for item_id in generator:
                    if item_id not in item_ids:
                        break
        return item_id
