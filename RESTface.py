import itertools
import operator
import re
import uuid
from urllib import parse

from inflect import engine
import dataset


# TODO:
# memory, sqlite, fs
# schemas set/validate
# autogenerate Swagger/OpenAPI specs
# example app using RESTface
# path of storage file json/sqlite

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

if storage_type == 'db':
    db = dataset.connect('sqlite:///:memory:')


def is_float(element) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def is_valid_uuid(obj) -> bool:
    try:
        uuid.UUID(obj)
        return True
    except ValueError:
        return False


def create_subhierarchy(parts) -> dict:
    parent_info = {}
    for i, part in enumerate(parts):
        # If part is item id
        if part.isdigit() or is_valid_uuid(part):
            if part.isdigit():
                part = int(part)
            if parts[i - 1] not in root:
                raise Exception('Invalid path')
            elif part not in root[parts[i - 1]]:
                root[parts[i - 1]][part] = {'id': part, **parent_info}
            parent_info = {engine.singular_noun(parts[i - 1]) + '_id': part}
        # If part is collection name
        else:
            # If no such collection then create it
            if part not in root:
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
    parts = parse.urlsplit(request['url']).path.strip('/').split('/')
    parent_info = create_subhierarchy(parts)

    part = parts[-1]
    if part.isdigit() or is_valid_uuid(part):
        if part.isdigit():
            part = int(part)

        if method == 'GET':
            return [root[parts[-2]][part]]
        elif method in {'POST', 'PUT'}:
            body = request.get('body', {})
            params = get_params(request)
            if method == 'PUT' or part not in root[parts[-2]]:
                root[parts[-2]][part] = {'id': part, **params, **body}
            # If method is POST and part is in collection
            else:
                root[parts[-2]][part].update(**params, **body)
            return part
        elif method == 'DELETE':
            return bool(root[parts[-2]].pop(part, None))
    else:
        if method == 'GET':
            items = list(root[part].values())
            params = get_params(request)

            # Filter by parent_id
            if len(parts) > 2:
                parent_id_name = engine.singular_noun(parts[-3]) + '_id'
                parent_id = parts[-2]
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
            ids = root[part].keys()
            # Come up with new id
            if not ids or type(list(ids)[0]) == int:
                generator = itertools.count(1)
            else:
                generator = (str(uuid.uuid4()) for _ in itertools.count())
            for i in generator:
                if i not in ids:
                    body = request.get('body', {})
                    params = get_params(request)
                    root[part][i] = {'id': i, **parent_info, **params, **body}
                    return i
        elif method == 'DELETE':
            return bool(root.pop(part, None))


def post(request):
    return handler(request, 'POST')


def get(request):
    return handler(request, 'GET')


def put(request):
    return handler(request, 'PUT')


def delete(request):
    return handler(request, 'DELETE')
