import re
from urllib import parse
from uuid import UUID

from inflect import engine


def parse_param(initial_param):
    param = initial_param.lower()
    if param == 'true':
        return True
    elif param == 'false':
        return False
    elif param.isdigit():
        return int(param)
    elif param in ('none', 'null'):
        return None
    try:
        return float(param)
    except ValueError:
        return initial_param


def parse_id(element: str):
    if element.isdigit():
        return int(element)
    try:
        UUID(element)
        return element
    except (ValueError, AttributeError):
        return None


class RESTface:
    def __init__(self, storage_type: str = 'memory', storage_path: str = None):
        if storage_type == 'memory':
            from storage.MemoryStorage import MemoryStorage
            self.storage = MemoryStorage()
        elif storage_type == 'db':
            from storage.DbStorage import DbStorage
            self.storage = DbStorage(storage_path)
        elif storage_type == 'file':
            from storage.FileStorage import FileStorage
            self.storage = FileStorage(storage_path)
        elif storage_type == 'mongo':
            from storage.MongoStorage import MongoStorage
            self.storage = MongoStorage(storage_path)
        self.engine = engine()

    def reset(self):
        self.storage.reset()

    def all(self):
        return self.storage.all()

    def create_subhierarchy(self, parts) -> dict:
        parent_info = {}
        for i, part in enumerate(parts):
            item_id = parse_id(part)
            if item_id:
                collection_name = parts[i - 1]
                if parse_id(collection_name):
                    raise Exception('Invalid path')
                data = [{'id': item_id, **parent_info}]
                if i != len(parts) - 1:
                    self.storage.post(collection_name, data)
                    parent_info = {self.engine.singular_noun(parts[i - 1]) + '_id': item_id}
        return parent_info

    def get_params(self, request) -> dict:
        url = request['url']
        query = parse.urlsplit(url).query
        params = parse.parse_qs(query, keep_blank_values=True)
        params = {
            param_name: parse_param(param_value[0])
            for param_name, param_value in params.items()
        }
        return params

    def handler(self, request, method):
        path = parse.urlsplit(request['url']).path
        url_parts = re.sub(r'^\d+', '', path).strip('/').split('/')
        last_part = url_parts[-1]
        item_id = parse_id(last_part)
        if item_id:
            collection_name = str(url_parts[-2])
        else:
            collection_name = str(last_part)

        if method == 'GET':
            if item_id:
                return self.storage.get_with_id(collection_name, item_id)
            else:
                params = self.get_params(request)
                order_by = params.pop('order_by', None) or params.pop('sort', None) or 'id'
                order_by = re.split(", ?", order_by.strip('({[]})'))
                meta_params = {
                    'order_by': order_by,
                    'desc': ('desc' in params),
                    '_limit': params.pop("limit", 0),
                    '_offset': params.pop("offset", 0)
                }
                params.pop('desc', None)

                # Filter by parent_id
                if len(url_parts) > 2:
                    parent_id_name = self.engine.singular_noun(url_parts[-3]) + '_id'
                    parent_id = url_parts[-2]
                    parent_id = parse_id(parent_id)
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
                        param_value = [parse_param(param) for param in param_value]
                    where_params += [[op_name, param_name, param_value]]

                items = self.storage.get_without_id(collection_name, where_params, meta_params)
                return items

        elif method in {'POST', 'PUT'}:
            parent_info = self.create_subhierarchy(url_parts)
            item_id = {'id': item_id} if item_id else {}
            params = self.get_params(request)
            body = request.get('body', {})
            if not body or type(body) == dict:
                data = [{**parent_info, **item_id, **params, **body}]
            else:
                data = [
                    {**parent_info, **item_id, **params, **item}
                    for item in body
                ]

            if method == 'POST':
                return self.storage.post(collection_name, data)
            else:
                return self.storage.put(collection_name, data)
        elif method == 'DELETE':
            return self.storage.delete(collection_name, item_id)

    def post(self, request):
        return self.handler(request, 'POST')

    def get(self, request):
        return self.handler(request, 'GET')

    def put(self, request):
        return self.handler(request, 'PUT')

    def delete(self, request):
        return self.handler(request, 'DELETE')
