import uuid
from typing import List, Union

import dataset

from .BaseStorage import BaseStorage


class DbStorage(BaseStorage):
    def __init__(self, storage_path: str = None, uuid_id: bool = False):
        storage_path = storage_path or 'sqlite:///:memory:'
        self.db = dataset.connect(storage_path, row_type=dict)
        self.primary_type = self.db.types.string if uuid_id else self.db.types.integer

    def get_with_id(self, table_name: str, item_id: Union[int, str]) -> dict:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        return table.find_one(id=item_id) or {}

    def get_without_id(self, table_name: str, where_params: list, meta_params: dict) -> list:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        where_params = {
            param_name: (
                {op_name: param_value} if param_value else {'not': None}
            )
            for op_name, param_name, param_value in where_params
        }
        if meta_params.pop('desc', False):
            meta_params['order_by'] = ['-' + order_by_arg.lstrip('-') for order_by_arg in meta_params['order_by']]
        if not meta_params['_limit']:
            meta_params.pop('_limit', None)
        params = {**where_params, **meta_params}
        items = list(table.find(**params))
        return items

    def post(self, table_name: str, data: List[dict]):
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        item_ids = []
        for item in data:
            if 'id' not in item and self.primary_type == self.db.types.string:
                existing_item_ids = {_item['id'] for _item in table.all()}
                while True:
                    item_id = str(uuid.uuid4())
                    if item_id not in existing_item_ids:
                        break
                item['id'] = item_id
            item_id = table.upsert(item, ['id'])
            item_ids.append(item_id)
        return item_ids

    def delete(self, table_name: str, item_id: Union[int, str] = None) -> bool:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        if item_id:
            existed = table.delete(id=item_id)
            return existed
        else:
            existed = table_name in self.db.tables
            table.drop()
            return existed

    def all(self) -> dict:
        return {
            table_name: list(self.db[table_name].all())
            for table_name in self.db.tables
        }

    def reset(self) -> None:
        for table in self.db.tables:
            self.db[table].drop()
