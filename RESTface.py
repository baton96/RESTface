import itertools
import operator
import re
from abc import ABC
from typing import Optional
from urllib import parse

import dataset
from inflect import engine


class Storage(ABC):
    pass


class MemoryStorage(Storage):
    def get_with_id(self, collection_name: str, item_id: int):
        collection = root[collection_name]
        return collection.get(item_id, {})

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


class DbStorage(Storage):
    def get_with_id(self, table_name: str, item_id: int):
        return db[table_name].find_one(id=item_id) or {}

    def post(self, table_name: str, data: Optional[dict] = None):
        data = data or {}
        # existing -> True, nonexisting -> id
        return db[table_name].upsert(data, ['id'])

    def put(self, table_name: str, data: Optional[dict] = None):
        data = data or {}
        item_id = data.get('id')
        db[table_name].delete(id=item_id)
        # existing -> True, nonexisting -> id
        return db[table_name].upsert(data, ['id'])

    def delete(self, table_name: str, item_id: Optional[int] = None) -> bool:
        if item_id:
            existed = db[table_name].delete(id=item_id)
            return existed
        else:
            existed = table_name in db.tables
            db[table_name].drop()
            return existed


# TODO:
# memory, sqlite, fs
# schemas set/validate
# autogenerate Swagger/OpenAPI specs
# example app using RESTface
# path of storage file json/sqlite
# uuid
# remove creating on get?

def get_ops() -> dict:
    op_names = ['eq', 'ge', 'gt', 'le', 'lt', 'ne']
    _ops = {
        op_name: operator.__getattribute__(op_name)
        for op_name in op_names
    }
    _ops['in'] = lambda a, b: str(a) in re.split(", ?", b.strip('({[]})'))
    _ops['gte'] = operator.ge
    _ops['lte'] = operator.le
    _ops['neq'] = operator.ne
    return _ops


storage_type = 'memory'  # db
engine = engine()
ops = get_ops()
root = {}

storage = MemoryStorage()
if storage_type == 'db':
    db = dataset.connect('sqlite:///:memory:', row_type=dict)


def is_float(element) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def create_subhierarchy(parts) -> dict:
    parent_info = {}
    for i, part in enumerate(parts):
        # If part is item id
        if part.isdigit():
            part = int(part)
            if parts[i - 1] not in root:
                raise Exception('Invalid path')
            elif part not in root[parts[i - 1]]:
                root[parts[i - 1]][part] = {'id': part, **parent_info}
            parent_info = {engine.singular_noun(parts[i - 1]) + '_id': part}
        # If part is collection name
        elif part not in root:
            root[part] = {}
    return parent_info


def get_params(request) -> dict:
    url = request['url']
    query = parse.urlsplit(url).query
    params = parse.parse_qs(query, keep_blank_values=True)
    for param_name in params.keys():
        param_value = params[param_name][0].lower()
        if param_value == 'true':
            param_value = True
        elif param_value == 'false':
            param_value = False
        elif param_value.isdigit():
            param_value = int(param_value)
        elif param_value in ('none', 'null'):
            param_value = None
        elif is_float(param_value):
            param_value = float(param_value)
        else:
            params[param_name] = params[param_name][0]
            continue
        params[param_name] = param_value
    return params


def handler(request, method):
    url_parts = parse.urlsplit(request['url']).path.strip('/').split('/')
    parent_info = create_subhierarchy(url_parts)

    last_part = url_parts[-1]
    if last_part.isdigit():
        collection_name = str(url_parts[-2])
        item_id = int(last_part)
    else:
        collection_name = str(last_part)
        item_id = None

    if method == 'GET':
        if item_id:
            return storage.get_with_id(collection_name, item_id)
        else:
            items = list(root[last_part].values())
            params = get_params(request)

            # Filter by parent_id
            if len(url_parts) > 2:
                parent_id_name = engine.singular_noun(url_parts[-3]) + '_id'
                parent_id = url_parts[-2]
                if parent_id.isdigit():
                    parent_id = int(parent_id)
                params[parent_id_name] = parent_id

            # Prepare for sorting
            sort_field = params.pop('sort', 'id')
            desc = 'desc' in params
            params.pop('desc', None)

            # Filtering by other fields
            for param_name, param_value in params.items():
                # Equality is the default comparision method
                if '__' not in param_name:
                    param_name = f'{param_name}__eq'
                field_name, op_name = param_name.split('__')
                op = ops[op_name]
                # Handle blank parameters
                if not param_value:
                    op = lambda field, _: field
                items = [item for item in items if op(item.get(field_name), param_value)]

            # Sorting, keep None but put it on the end of results
            sort_by = lambda item: ((value := item.get(sort_field)) is None, value)
            items = sorted(items, key=sort_by, reverse=desc)

            return items
    elif method in {'POST', 'PUT'}:
        params = get_params(request)
        body = request.get('body', {})
        if item_id:
            data = {'id': item_id, **params, **body}
        else:
            data = {**parent_info, **params, **body}
        if method == 'POST':
            return storage.post(collection_name, data)
        else:
            return storage.put(collection_name, data)
    elif method == 'DELETE':
        return storage.delete(collection_name, item_id)


def post(request):
    return handler(request, 'POST')


def get(request):
    return handler(request, 'GET')


def put(request):
    return handler(request, 'PUT')


def delete(request):
    return handler(request, 'DELETE')
