import dataset

from .BaseStorage import BaseStorage
db = {}


class DbStorage(BaseStorage):
    def __init__(self, storage_path: str = None):
        global db
        storage_path = storage_path or 'sqlite:///:memory:'
        db = dataset.connect(storage_path, row_type=dict)

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
            meta_params['order_by'] = ['-' + order_by_arg.lstrip('-') for order_by_arg in meta_params['order_by']]
        if not meta_params['_limit']:
            meta_params.pop('_limit', None)
        params = {**where_params, **meta_params}
        items = list(db[table_name].find(**params))
        return items

    def post(self, table_name: str, data: dict):
        return db[table_name].upsert(data, ['id'])

    def put(self, table_name: str, data: dict):
        item_id = data.get('id')
        db[table_name].delete(id=item_id)
        return db[table_name].insert(data)

    def delete(self, table_name: str, item_id: int = None) -> bool:
        if item_id:
            existed = db[table_name].delete(id=item_id)
            return existed
        else:
            existed = table_name in db.tables
            db[table_name].drop()
            return existed

    def all(self):
        return {table: {row['id']: row for row in db[table].all()} for table in db.tables}

    def reset(self):
        for table in db.tables:
            db[table].drop()
