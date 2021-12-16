import re
from urllib import parse

import dataset
from inflect import engine
from storage import MemoryStorage, DbStorage

# TODO:
# memory, sqlite, fs
# schemas set/validate
# autogenerate Swagger/OpenAPI specs
# example app using RESTface
# path of storage file json/sqlite
# uuid
# sort by two criteria
# multiple op on same param

storage_type = 'memory'  # memory / db
engine = engine()

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
