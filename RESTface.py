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
            op = ops[op_name]
        else:
            op = lambda field, _: field is not None
        return op(item.get(param_name), param_value)


class DbStorage(Storage):
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


# TODO:
# memory, sqlite, fs
# schemas set/validate
# autogenerate Swagger/OpenAPI specs
# example app using RESTface
# path of storage file json/sqlite
# uuid
# sort by two criteria
# multiple op on same param

def get_ops() -> dict:
    op_names = ['eq', 'ge', 'gt', 'le', 'lt', 'ne']
    _ops = {
        op_name: operator.__getattribute__(op_name)
        for op_name in op_names
    }
    _ops.update({
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
    return _ops


storage_type = 'memory'  # memory / db
engine = engine()
ops = get_ops()
root = {}

if storage_type == 'memory':
    storage = MemoryStorage()
if storage_type == 'db':
    db = dataset.connect('sqlite:///:memory:', row_type=dict)
    storage = DbStorage()


def is_float(element) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


# TODO: Not used anywhere
def get_parents_info(url_parts):
    offset = int(url_parts[-1].isdigit())
    if len(url_parts) > 2 + offset:
        collection_name = url_parts[-3 - offset]
        if collection_name not in root:
            root[collection_name] = {}
        parent_id_name = engine.singular_noun(collection_name) + '_id'
        parent_id = int(url_parts[-2 - offset])
        return {parent_id_name: parent_id}
    else:
        return {}


def create_subhierarchy(parts) -> dict:
    parent_info = {}
    for i, part in enumerate(parts):
        if part.isdigit():
            item_id = int(part)
            data = {'id': item_id, **parent_info}

            collection_name = parts[i - 1]
            if collection_name.isdigit():
                raise Exception('Invalid path')

            storage.post(collection_name, data)
            parent_info = {engine.singular_noun(parts[i - 1]) + '_id': item_id}
        else:
            collection_name = part
            storage.create_if_not_exists(collection_name)
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
    path = parse.urlsplit(request['url']).path
    url_parts = re.sub(r'^\d+', '', path).strip('/').split('/')
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
            params = get_params(request)
            order_by = params.pop('order_by', None) or params.pop('sort', None) or 'id'
            meta_params = {
                'order_by': order_by.lstrip('-'),
                'desc': ('desc' in params) or order_by.startswith('-'),
                '_limit': params.pop("limit", None),
                '_offset': params.pop("offset", 0)
            }
            params.pop('desc', None)

            # Filter by parent_id
            if len(url_parts) > 2:
                parent_id_name = engine.singular_noun(url_parts[-3]) + '_id'
                parent_id = url_parts[-2]
                if parent_id.isdigit():
                    parent_id = int(parent_id)
                params[parent_id_name] = parent_id

            where_params = []
            # Filtering by other fields
            for param_name, param_value in params.items():
                if '__' in param_name:
                    param_name, op_name = param_name.split('__')
                else:
                    op_name = '='
                if op_name in {'between', 'notin', 'in'}:
                    param_value = re.split(", ?", param_value.strip('({[]})'))
                where_params += [[op_name, param_name, param_value]]

            items = storage.get_without_id(collection_name, where_params, meta_params)
            return items

    elif method in {'POST', 'PUT'}:
        parent_info = create_subhierarchy(url_parts)
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
