import csv
import re
from io import StringIO
from json import loads
from uuid import UUID

import yaml
from flask import request, jsonify, Response
from inflect import engine as get_engine


def get_storage(
    storage_type: str = "memory", storage_path: str | None = None, uuid_id: bool = False
):
    if storage_type == "memory":
        from storage.MemoryStorage import MemoryStorage

        return MemoryStorage(uuid_id)
    elif storage_type == "db":
        from storage.DbStorage import DbStorage

        return DbStorage(storage_path, uuid_id)
    elif storage_type == "file":
        from storage.FileStorage import FileStorage

        return FileStorage(storage_path, uuid_id)
    elif storage_type == "mongo":
        from storage.MongoStorage import MongoStorage

        return MongoStorage(storage_path, uuid_id)
    elif storage_type == "redis":
        from storage.RedisStorage import RedisStorage

        return RedisStorage(storage_path, uuid_id)
    else:
        raise Exception("Unknown storage type")


def parse_param(obj):
    try:
        return loads(obj)
    except ValueError:
        return obj


def parse_id(element: str):
    if element.isdigit():
        return int(element)
    try:
        UUID(element)
        return element
    except (ValueError, AttributeError):
        return None


def to_yaml(obj):
    return yaml.dump(obj)


def _to_xml(obj, tag: str) -> str:
    if isinstance(obj, dict):
        items = "".join(_to_xml(v, k) for k, v in obj.items())
        return f"<{tag}>{items}</{tag}>"
    elif isinstance(obj, list):
        return "".join(_to_xml(item, tag) for item in obj)
    else:
        return f"<{tag}>{obj}</{tag}>"


def to_xml(obj, collection_name: str) -> str:
    engine = get_engine()
    item_name = engine.singular_noun(collection_name) or collection_name
    if isinstance(obj, list):
        items = "".join(_to_xml(item, item_name) for item in obj)
        return f"<{collection_name}>{items}</{collection_name}>"
    elif isinstance(obj, dict):
        return _to_xml(obj, item_name)
    else:
        raise Exception("Cannot format to XML")


def flatten_dict(d, parent_key=""):
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            yield from dict(flatten_dict(v, new_key)).items()
        else:
            yield new_key, v


def to_csv(obj) -> str:
    objects = [obj] if isinstance(obj, dict) else obj
    objects = [dict(flatten_dict(obj)) for obj in objects]
    keys = sorted(set(key for obj in objects for key in obj.keys()))
    with StringIO() as tmp_file:
        writer = csv.writer(tmp_file)
        writer.writerow(keys)
        writer.writerows((obj.get(key) for key in keys) for obj in objects)
        return tmp_file.getvalue()


def get_collection_name(path):
    url_parts = re.sub(r"^\d+", "", path).strip("/").split("/")
    last_part = url_parts[-1]
    item_id = parse_id(last_part)
    if item_id:
        collection_name = str(url_parts[-2])
    else:
        collection_name = str(last_part)
    return collection_name


def reformat(result):
    collection_name = get_collection_name(request.path)
    response_format = request.args.get("format")
    if response_format == "csv":
        return Response(
            to_csv(result),
            mimetype="text/csv",
            headers={"Content-Disposition": f"filename={collection_name}.csv"},
        )
    elif response_format == "xml":
        return Response(to_xml(result, collection_name), mimetype="text/xml")
    elif response_format == "yaml":
        return Response(to_yaml(result), mimetype="text/yaml")
    else:
        return jsonify(result)
