import pytest
from fastapi import HTTPException


@pytest.fixture
def items(face):
    for i in range(1, 5):
        face.post("https://example.com/users")


@pytest.fixture
def items_with_children(face):
    for i in range(4):
        face.post(f"https://example.com/users/{(i % 2) + 1}/posts")


@pytest.fixture
def items_unsorted(face):
    for i in [21, 3, 19, 37, 28]:
        face.post(f"https://example.com/users/{i}")


def test_get_all(face, items):
    assert face.get("https://example.com/users") == [{"id": i} for i in range(1, 5)]


def test_get_by_id(face, items):
    assert face.get("https://example.com/users/1") == {"id": 1}
    assert face.get("https://example.com/users?id=1") == [{"id": 1}]


def test_lte(face, items):
    assert face.get("https://example.com/users?id__lt=3") == [{"id": 1}, {"id": 2}]
    assert face.get("https://example.com/users?id__lte=2") == [{"id": 1}, {"id": 2}]


def test_in(face, items):
    assert face.get("https://example.com/users?id__in=(1,2)") == [{"id": 1}, {"id": 2}]
    assert face.get("https://example.com/users?id__in={1, 2}") == [{"id": 1}, {"id": 2}]
    assert face.get("https://example.com/users?id__in=[1, 2]") == [{"id": 1}, {"id": 2}]


def test_children(face, items_with_children):
    assert face.get("https://example.com/users/1/posts") == [
        {"id": 1, "user_id": 1},
        {"id": 3, "user_id": 1},
    ]


def test_children_custom(face, items_with_children):
    assert face.get("https://example.com/users/1/posts?id__lt=2") == [
        {"id": 1, "user_id": 1}
    ]


def test_sort(face, items_unsorted):
    assert face.get("https://example.com/users?order_by=id") == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28])
    ]


def test_sort_desc(face, items_unsorted):
    assert face.get("https://example.com/users?order_by=id&desc") == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28], reverse=True)
    ]
    assert face.get("https://example.com/users?desc") == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28], reverse=True)
    ]


def test_sort_blank(face, items_unsorted):
    assert face.get("https://example.com/users") == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28])
    ]


def test_blank_param(face):
    for i in range(1, 5):
        url = "https://example.com/users"
        if i % 2:
            url += f"?is_odd={'true' if i % 3 else 'false'}"
        face.post(url)
    assert face.get("https://example.com/users?is_odd") == [
        {"id": 1, "is_odd": True},
        {"id": 3, "is_odd": False},
    ]


def test_blank_param_no_field(face):
    for i in range(1, 5):
        url = "https://example.com/users"
        if i % 2:
            url += "?is_odd=true"
        face.post(url)
    assert face.get("https://example.com/users?is_odd") == [
        {"id": 1, "is_odd": True},
        {"id": 3, "is_odd": True},
    ]


def test_sort_none(face):
    for i in range(1, 5):
        face.post(f"https://example.com/users?noneable={i if i % 2 else 'null'}")
    assert face.get("https://example.com/users?order_by=noneable") == [
        {"id": 2, "noneable": None},
        {"id": 4, "noneable": None},
        {"id": 1, "noneable": 1},
        {"id": 3, "noneable": 3},
    ]


def test_sort_multiple(face):
    for a in [0, 1]:
        for b in [0, 1]:
            face.post(f"https://example.com/users?a={1 - a}&b={1 - b}")
            face.post(f"https://example.com/users?a={1 - a}&b={1 - b}")
    assert face.get("https://example.com/users?order_by=a,b") == [
        {"id": 7, "a": 0, "b": 0},
        {"id": 8, "a": 0, "b": 0},
        {"id": 5, "a": 0, "b": 1},
        {"id": 6, "a": 0, "b": 1},
        {"id": 3, "a": 1, "b": 0},
        {"id": 4, "a": 1, "b": 0},
        {"id": 1, "a": 1, "b": 1},
        {"id": 2, "a": 1, "b": 1},
    ]


def test_offset(face, items):
    assert face.get("https://example.com/users?offset=1") == [
        {"id": i} for i in range(2, 5)
    ]


def test_offset_limit(face, items):
    assert face.get("https://example.com/users?offset=1&limit=2") == [
        {"id": i} for i in range(2, 4)
    ]


def test_only_names(face):
    assert face.get("https://example.com/users/posts") == []


def test_only_ids(face):
    with pytest.raises(HTTPException):
        face.get("https://example.com/1/2")


def test_nonexisting(face):
    with pytest.raises(HTTPException):
        face.get("https://example.com/users/1")
