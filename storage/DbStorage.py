from typing import Optional
import dataset


db = {}


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
