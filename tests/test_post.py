import uuid
import warnings
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from utils import parse_id

"""def is_valid_uuid(element):
    try:
        uuid.UUID(element)
        return True
    except (ValueError, AttributeError):
        return False"""


def test_simple_no_id(face):
    assert face.post("https://example.com/users") == 1
    assert face.all() == {"users": [{"id": 1}]}


def test_simple_int_id(face):
    assert face.post("https://example.com/users/1") == 1
    assert face.all() == {"users": [{"id": 1}]}
    assert face.post("https://example.com/users") == 2
    assert face.all() == {"users": [{"id": 1}, {"id": 2}]}


def test_simple_uuid_id(face):
    face.storage = face.storage.__class__(uuid_id=True)

    item_id = str(uuid.uuid4())
    assert face.post(f"https://example.com/users/{item_id}") == item_id
    assert face.all() == {"users": [{"id": item_id}]}

    new_item_id = face.post("https://example.com/users")
    assert parse_id(new_item_id)
    assert sorted(face.all()["users"], key=lambda item: item["id"]) == sorted(
        [{"id": item_id}, {"id": new_item_id}], key=lambda item: item["id"]
    )


def test_simple_child_no_id(face):
    assert face.post("https://example.com/users/1/posts") == 1
    assert face.all() == {"users": [{"id": 1}], "posts": [{"id": 1, "user_id": 1}]}


def test_simple_child_id(face):
    face.post("https://example.com/users/1/posts/2")
    assert face.all() == {"users": [{"id": 1}], "posts": [{"id": 2, "user_id": 1}]}


def test_simple_deep(face):
    face.post("https://example.com/users/1/posts/2/comments/3")
    assert face.all() == {
        "users": [{"id": 1}],
        "posts": [{"id": 2, "user_id": 1}],
        "comments": [{"id": 3, "post_id": 2}],
    }


def test_simple_url_data(face):
    face.post("https://example.com/users?name=myname")
    assert face.all() == {"users": [{"id": 1, "name": "myname"}]}


def test_simple_body_data(face):
    face.post("https://example.com/users", {"name": "myname"})
    assert face.all() == {"users": [{"id": 1, "name": "myname"}]}


def test_child_url_data(face):
    face.post("https://example.com/users/1/posts/2?name=myname")
    assert face.all() == {
        "users": [{"id": 1}],
        "posts": [{"id": 2, "user_id": 1, "name": "myname"}],
    }


def test_child_body_data(face):
    face.post("https://example.com/users/1/posts/2", {"name": "myname"})
    assert face.all() == {
        "users": [{"id": 1}],
        "posts": [{"id": 2, "user_id": 1, "name": "myname"}],
    }


def test_modify_post(face):
    face.post("https://example.com/users/1?a=b")
    assert face.all() == {"users": [{"id": 1, "a": "b"}]}
    face.post("https://example.com/users/1?c=d")
    assert face.all() == {"users": [{"id": 1, "a": "b", "c": "d"}]}


def test_modify_put(face):
    if face.storage.__class__.__name__ == "DbStorage":
        warnings.warn("PUT method is not implemented for DbStorage")
        return
    face.put("https://example.com/users/1?a=b")
    assert face.all() == {"users": [{"id": 1, "a": "b"}]}
    face.put("https://example.com/users/1?c=d")
    assert face.all() == {"users": [{"id": 1, "c": "d"}]}


def test_param_types(face):
    params = {
        "int": "1",
        "float": "0.5",
        "str": "value",
        "true": "true",
        "false": "false",
        "null": "null",
        "empty": "",
    }
    params = "&".join(f"{name}={value}" for name, value in params.items())
    face.post(f"https://example.com/users?{params}")
    assert face.all()["users"][0] == {
        "id": 1,
        "int": 1,
        "float": 0.5,
        "str": "value",
        "true": True,
        "false": False,
        "null": None,
        "empty": "",
    }


def test_same_params(face):
    face.post("https://example.com/users/1?a=b&a=c")
    assert face.all() == {"users": [{"id": 1, "a": "b"}]}


def test_only_names(face):
    assert face.post("https://example.com/users/posts") == 1
    assert face.all() == {"posts": [{"id": 1}]}


def test_only_ids(face):
    with pytest.raises(Exception):
        face.post("https://example.com/1/2")


def test_bulk(face):
    assert face.post("https://example.com/users", [{"name": "a"}, {"name": "b"}]) == [
        1,
        2,
    ]
    assert face.all() == {"users": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}


def test_bulk_existing(face):
    assert face.post("https://example.com/users", [{"name": "a"}, {"name": "b"}]) == [
        1,
        2,
    ]
    assert face.post(
        "https://example.com/users", [{"id": 1, "name": "c"}, {"id": 2, "name": "d"}]
    ) == [1, 2]
    assert face.all() == {"users": [{"id": 1, "name": "c"}, {"id": 2, "name": "d"}]}


def test_bulk_partially_existing(face):
    assert face.post("https://example.com/users", [{"name": "a"}, {"name": "b"}]) == [
        1,
        2,
    ]
    assert face.post(
        "https://example.com/users", [{"id": 1, "name": "c"}, {"name": "d"}]
    ) == [1, 3]
    assert face.all() == {
        "users": [
            {"id": 1, "name": "c"},
            {"id": 2, "name": "b"},
            {"id": 3, "name": "d"},
        ]
    }


def test_upload(face):
    file = FileStorage(filename="users.csv", stream=BytesIO(b"id,name\n1,a\n2,b"))
    face.upload(file)
    assert face.all() == {
        "users": [
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
        ]
    }
