import pytest
from werkzeug.exceptions import NotFound


@pytest.fixture(autouse=True)
def item(face):
    face.post("https://example.com/users")
    assert face.all() == {"users": [{"id": 1}]}


def test_delete_one_existing(face):
    face.delete("https://example.com/users/1")
    assert face.all() == {"users": []}


def test_delete_nonexisting(face):
    with pytest.raises(NotFound):
        face.delete("https://example.com/users/2")


def test_delete_all_existing(face):
    face.delete("https://example.com/users")
    assert face.all() == {}


def test_delete_all_nonexisting(face):
    face.delete("https://example.com/users")
    face.delete("https://example.com/users")
    assert face.all() == {}


def test_delete_one_where_cond(face):
    face.delete("https://example.com/users?id=1")
    assert face.all() == {"users": []}
