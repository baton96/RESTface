import itertools
import operator
import re
import uuid
from urllib import parse

from inflect import engine

engine = engine()
_root = {}

op_names = ['eq', 'ge', 'gt', 'le', 'lt', 'ne']
ops = {
    op_name: operator.__getattribute__(op_name)
    for op_name in op_names
}
ops['in'] = lambda a, b: str(a) in re.split(", ?", b.strip('({[]})'))
ops['gte'] = operator.ge
ops['lte'] = operator.le
ops['neq'] = operator.ne


# TODO: blank parameters in POST and GET
def is_valid_uuid(obj):
    try:
        uuid.UUID(obj)
        return True
    except (ValueError, AttributeError):
        return False


def create_subhierarchy(parts, root):
    parent_info = {}
    for i, part in enumerate(parts):
        # If part is item id
        if part.isdigit() or is_valid_uuid(part):
            if part.isdigit():
                part = int(part)
            if part not in root[parts[i - 1]]:
                root[parts[i - 1]][part] = {'id': part, **parent_info}
            parent_info = {engine.singular_noun(parts[i - 1]) + '_id': part}
        # If part is collection name
        else:
            # If no such collection then create it
            if part not in root:
                root[part] = {}
    return parent_info


def get_params(request):
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
        else:
            params[param_name] = params[param_name][0]
            continue
        params[param_name] = param_value
    return params


def handler(request, method, root=None):
    if root is None:
        root = _root
    parts = parse.urlsplit(request['url']).path.strip('/').split('/')
    parent_info = create_subhierarchy(parts, root)

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
            # method == 'POST and part in collection
            else:
                root[parts[-2]][part].update(**params, **body)
            return root[parts[-2]][part]
        elif method == 'DELETE':
            root[parts[-2]].pop(part, None)
    else:
        if method == 'GET':
            items = list(root[part].values())
            params = get_params(request)
            if len(parts) > 2:
                parent_id_name = engine.singular_noun(parts[-3]) + '_id'
                parent_id = parts[-2]
                if parent_id.isdigit():
                    parent_id = int(parent_id)
                params[parent_id_name] = parent_id
            for param_name, param_value in params.items():
                if '__' not in param_name:
                    param_name = f'{param_name}__eq'
                field_name, op_name = param_name.split('__')
                op = ops[op_name]
                items = [item for item in items if op(item[field_name], param_value)]
            return items
        elif method in {'POST', 'PUT'}:
            ids = root[part].keys()
            for i in itertools.count(1):
                if i not in ids:
                    body = request.get('body', {})
                    params = get_params(request)
                    root[part][i] = {'id': i, **parent_info, **params, **body}
                    return root[part][i]
        elif method == 'DELETE':
            root.pop(part, None)


def post(request, root=None):
    return handler(request, 'POST', root)


def get(request, root=None):
    return handler(request, 'GET', root)


def put(request, root=None):
    return handler(request, 'PUT', root)


def delete(request, root=None):
    return handler(request, 'DELETE', root)
