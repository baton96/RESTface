import re
from urllib import parse

from inflect import engine as get_engine

from openapi import get_schema
from storage.DbStorage import DbStorage
from utils import get_storage, parse_param, parse_id


class RESTface:
    def __init__(
        self,
        storage_type: str = "db",
        storage_path: str = None,
        uuid_id: bool = False,
    ):
        self.storage = get_storage(storage_type, storage_path, uuid_id)
        self.engine = get_engine()

    def reset(self):
        self.storage.reset()

    def all(self):
        return self.storage.all()

    def openapi(self):
        if not isinstance(self.storage, DbStorage):
            raise NotImplementedError
        return get_schema(self.storage.db, self.engine)

    def receive_file(self, request):
        file = next(iter(request.files.values()))
        # stream = file.stream.read().decode("utf-8")
        name = file.filename
        if name.endswith(".json"):
            pass
        elif name.endswith(".csv"):
            pass
        elif name.endswith(".xml"):
            pass
        elif name.endswith(".yaml"):
            pass

    def create_subhierarchy(self, parts) -> dict:
        parent_info = {}
        for i, part in enumerate(parts):
            item_id = parse_id(part)
            if item_id:
                collection_name = parts[i - 1]
                if parse_id(collection_name):
                    raise Exception("Invalid path")
                data = {"id": item_id, **parent_info}
                if i != len(parts) - 1:
                    self.storage.put_n_post(collection_name, data, "POST")
                    parent_info = {
                        self.engine.singular_noun(parts[i - 1]) + "_id": item_id
                    }
        return parent_info

    def get_params(self, request) -> dict:
        url = request["url"]
        query = parse.urlsplit(url).query
        params = parse.parse_qs(query, keep_blank_values=True)
        params = {
            param_name: parse_param(param_value[0])
            for param_name, param_value in params.items()
        }
        return params

    def handler(self, request, method):
        path = parse.urlsplit(request["url"]).path
        url_parts = re.sub(r"^\d+", "", path).strip("/").split("/")
        last_part = url_parts[-1]
        item_id = parse_id(last_part)
        if item_id:
            collection_name = str(url_parts[-2])
        else:
            collection_name = str(last_part)

        if method == "GET":
            if item_id:
                return self.storage.get_with_id(collection_name, item_id)
            else:
                params = self.get_params(request)
                if "id" in params:
                    item = self.storage.get_with_id(collection_name, params["id"])
                    return [item] if item else []
                order_by = (
                    params.pop("order_by", None) or params.pop("sort", None) or "id"
                )
                order_by = re.split(", ?", order_by.strip("({[]})"))
                meta_params = {
                    "order_by": order_by,
                    "desc": ("desc" in params),
                    "_limit": params.pop("limit", 0),
                    "_offset": params.pop("offset", 0),
                }
                params.pop("desc", None)

                # Filter by parent_id
                if len(url_parts) > 2:
                    parent_id_name = self.engine.singular_noun(url_parts[-3]) + "_id"
                    parent_id = url_parts[-2]
                    parent_id = parse_id(parent_id)
                    params[parent_id_name] = parent_id

                where_params = []
                # Filtering by other fields
                for param_name, param_value in params.items():
                    if "__" in param_name:
                        param_name, op_name = param_name.split("__")
                    else:
                        op_name = "="
                    if op_name in {"between", "notin", "in"}:
                        param_value = re.split(", ?", str(param_value).strip("({[]})"))
                        param_value = [parse_param(param) for param in param_value]
                    where_params += [[op_name, param_name, param_value]]

                items = self.storage.get_without_id(
                    collection_name, where_params, meta_params
                )
                return items

        elif method in ("POST", "PUT"):
            parent_info = self.create_subhierarchy(url_parts)
            item_id = {"id": item_id} if item_id else {}
            params = self.get_params(request)
            body = request.get("body", {})
            if isinstance(body, list):
                if parent_info or params:
                    body = [{**parent_info, **params, **item} for item in body]
                # body.sort(key=lambda item: ('id' not in item, item.get('id')))
                return self.storage.bulk_put_n_post(collection_name, body, method)
            elif isinstance(body, dict):
                data = {**parent_info, **item_id, **params, **body}
                return self.storage.put_n_post(collection_name, data, method)
            else:
                raise Exception("Body has to be valid JSON")
        elif method == "DELETE":
            params = self.get_params(request)
            if item_id or "id" in params:
                self.storage.delete(collection_name, [], item_id or params["id"])
                return
            # Filter by parent_id
            if len(url_parts) > 2:
                parent_id_name = self.engine.singular_noun(url_parts[-3]) + "_id"
                parent_id = url_parts[-2]
                parent_id = parse_id(parent_id)
                params[parent_id_name] = parent_id

            where_params = []
            # Filtering by other fields
            for param_name, param_value in params.items():
                if "__" in param_name:
                    param_name, op_name = param_name.split("__")
                else:
                    op_name = "="
                if op_name in {"between", "notin", "in"}:
                    param_value = re.split(", ?", str(param_value).strip("({[]})"))
                    param_value = [parse_param(param) for param in param_value]
                where_params += [[op_name, param_name, param_value]]
            self.storage.delete(collection_name, where_params)

    def post(self, request):
        return self.handler(request, "POST")

    def get(self, request):
        return self.handler(request, "GET")

    def put(self, request):
        return self.handler(request, "PUT")

    def delete(self, request):
        return self.handler(request, "DELETE")
