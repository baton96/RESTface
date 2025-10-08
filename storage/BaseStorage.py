import operator
import re
import uuid
from abc import ABC, abstractmethod


class BaseStorage(ABC):
    def __init__(self, _: str = None, uuid_id: bool = False):
        self.primary_type = str if uuid_id else int

        op_names = ["eq", "ge", "gt", "le", "lt", "ne"]
        self.ops = {op_name: getattr(operator, op_name) for op_name in op_names}
        self.ops.update(
            {
                "between": lambda item, collection: collection[0]
                <= item
                <= collection[-1],
                "ilike": lambda string, pattern: re.search(
                    pattern, str(string).lower()
                ),
                "like": lambda string, pattern: re.search(pattern, str(string)),
                "startswith": lambda string, pattern: str(string).startswith(pattern),
                "endswith": lambda string, pattern: str(string).endswith(pattern),
                "notin": lambda item, collection: item not in collection,
                "in": lambda item, collection: item in collection,
                "gte": operator.ge,
                "lte": operator.le,
                "neq": operator.ne,
                "not": operator.ne,
                "=": operator.eq,
            }
        )

    @abstractmethod
    def get_with_id(self, table_name: str, item_id: int | str) -> dict:
        pass

    def fulfill_cond(self, item, parsed_param):
        op_name, param_name, param_value = parsed_param
        if param_value:
            op = self.ops[op_name]
        else:

            def op(field, _):
                return field is not None

        return op(item.get(param_name), param_value)

    def get_without_id(
        self, table_name: str, where_params: list, meta_params: dict
    ) -> list:
        items = [
            item
            for item in self.get_items(table_name)
            if all(
                self.fulfill_cond(item, param)
                for param in where_params
            )
        ]

        # Sorting, keep None-s and put them on the beginning of results
        order_by = meta_params["order_by"]

        def order_key(item):
            return tuple(
                [
                    ((value := item.get(order_by_arg.lstrip("-"))) is not None, value)
                    for order_by_arg in order_by
                ]
                + [item["id"]]
            )

        desc = meta_params["desc"]
        items = sorted(items, key=order_key, reverse=desc)

        offset = meta_params["_offset"]
        limit = meta_params["_limit"] or len(items) - offset
        return items[offset : offset + limit]

    @abstractmethod
    def put_n_post(
        self, table_name: str, data: dict, method: str = "POST"
    ) -> int | str:
        pass

    # @abstractmethod
    def bulk_put_n_post(
        self, table_name: str, items: list[dict], method: str = "POST"
    ) -> list[int | str]:
        pass

    @abstractmethod
    def delete(
        self, table_name: str, where_params: list, item_id: int | str = None
    ) -> None:
        pass

    @abstractmethod
    def all(self):
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    def get_ids(self, collection_name: str) -> set:
        pass

    def get_items(self, collection_name: str) -> list[dict]:
        pass

    def get_id(self, collection_name: str, data: dict) -> int | str:
        item_id = data.get("id")
        if not item_id:
            if self.primary_type is int:
                item_ids = self.get_ids(collection_name)
                item_id = max(item_ids or {0}) + 1
            elif self.primary_type is str:
                item_id = str(uuid.uuid4())
            data["id"] = item_id
        return item_id

    def bulk_get_ids(self, collection_name: str, items: list[dict]) -> list[int | str]:
        if self.primary_type is int:
            item_ids = self.get_ids(collection_name)
            cur_max = max(item_ids or {0}) + 1
        else:
            cur_max = None
        for item in items:
            item_id = item.get("id")
            if not item_id:
                if self.primary_type is int:
                    item_id = cur_max
                    cur_max += 1
                elif self.primary_type is str:
                    item_id = str(uuid.uuid4())
                item["id"] = item_id
        item_ids = [item["id"] for item in items]
        return item_ids
