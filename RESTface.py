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


def post(request, root=None, method='POST'):
    if root is None:
        root = _root
    url = request['url']
    parts = parse.urlsplit(url).path.split('/')[1:]
    # Remove '/' from the end of url
    if not parts[-1]:
        parts.pop()

    meta = {}
    for i, part in enumerate(parts):
        # If part is item id
        if part.isdigit() or is_valid_uuid(part):
            if part.isdigit():
                part = int(part)
            # If it's last part
            if i == len(parts) - 1:
                body = request.get('body', {})
                params = get_params(request)
                if method == 'PUT' or part not in root[parts[i - 1]]:
                    root[parts[i - 1]][part] = {'id': part, **meta, **params, **body}
                # method == 'POST and part in collection
                else:
                    root[parts[i - 1]][part].update(**meta, **params, **body)
                return root[parts[i - 1]][part]
            # If not the last part
            else:
                if part not in root[parts[i - 1]]:
                    root[parts[i - 1]][part] = {'id': part}
                root[parts[i - 1]][part].update(meta)
                meta = {engine.singular_noun(parts[i - 1]) + '_id': part}

        # If part is collection name
        else:
            # If no such collection then create it
            if part not in root:
                root[part] = {}
            # If it's last part
            if i == len(parts) - 1:
                # Come up with unique id
                ids = root[part].keys()
                for i in itertools.count(1):
                    if i not in ids:
                        body = request.get('body', {})
                        params = get_params(request)
                        root[part][i] = {'id': i, **meta, **params, **body}
                        return root[part][i]


def get(request, root=None):
    if root is None:
        root = _root
    parts = parse.urlsplit(request['url']).path.split('/')[1:]
    if not parts[-1]:
        parts.pop()
    part = parts[-1]
    if part.isdigit() or is_valid_uuid(part):
        if part.isdigit():
            part = int(part)
        return [root[parts[-2]][part]]
    else:
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


def delete(request, root=None):
    if root is None:
        root = _root
    parts = parse.urlsplit(request['url']).path.split('/')[1:]
    if not parts[-1]:
        parts.pop()
    part = parts[-1]
    if part.isdigit() or is_valid_uuid(part):
        if part.isdigit():
            part = int(part)
        root[parts[-2]].pop(part, None)
    else:
        root.pop(part, None)
