import uuid

import dataset

from .BaseStorage import BaseStorage
db = {}


class DbStorage(BaseStorage):
    def __init__(self, storage_path: str = None, uuid_id: bool = False):
        global db
        storage_path = storage_path or 'sqlite:///:memory:'
        db = dataset.connect(storage_path, row_type=dict)
        self.primary_type = db.types.string if uuid_id else db.types.integer

    def get_with_id(self, table_name: str, item_id: int):
        table = db.get_table(table_name, primary_type=self.primary_type)
        return table.find_one(id=item_id) or {}

    def get_without_id(self, table_name: str, where_params: list, meta_params: dict):
        table = db.get_table(table_name, primary_type=self.primary_type)
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

    def post(self, table_name: str, data: dict):
        table = db.get_table(table_name, primary_type=self.primary_type)
        if 'id' not in data and self.primary_type == db.types.string:
            item_ids = {item['id'] for item in table.all()}
            while True:
                item_id = str(uuid.uuid4())
                if item_id not in item_ids:
                    break
            data['id'] = item_id
        return table.upsert(data, ['id'])

    def delete(self, table_name: str, item_id: int = None) -> bool:
        table = db.get_table(table_name, primary_type=self.primary_type)
        if item_id:
            existed = table.delete(id=item_id)
            return existed
        else:
            existed = table_name in db.tables
            table.drop()
            return existed

    def all(self):
        return {table: {row['id']: row for row in db[table].all()} for table in db.tables}

    def reset(self):
        for table in db.tables:
            db[table].drop()
