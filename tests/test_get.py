import pytest
from werkzeug.exceptions import NotFound


@pytest.fixture
def items(face):
    for i in range(1, 5):
        request = {"url": "https://example.com/users"}
        face.post(request)


@pytest.fixture
def items_with_children(face):
    for i in range(4):
        request = {"url": f"https://example.com/users/{(i % 2) + 1}/posts"}
        face.post(request)


@pytest.fixture
def items_unsorted(face):
    for i in [21, 3, 19, 37, 28]:
        request = {"url": f"https://example.com/users/{i}"}
        face.post(request)


def test_get_all(face, items):
    request = {"url": "https://example.com/users"}
    assert face.get(request) == [{"id": i} for i in range(1, 5)]


def test_get_by_id(face, items):
    request = {"url": "https://example.com/users/1"}
    assert face.get(request) == {"id": 1}
    request = {"url": "https://example.com/users?id=1"}
    assert face.get(request) == [{"id": 1}]


def test_lte(face, items):
    request = {"url": "https://example.com/users?id__lt=3"}
    assert face.get(request) == [{"id": 1}, {"id": 2}]
    request = {"url": "https://example.com/users?id__lte=2"}
    assert face.get(request) == [{"id": 1}, {"id": 2}]


def test_in(face, items):
    request = {"url": "https://example.com/users?id__in=(1,2)"}
    assert face.get(request) == [{"id": 1}, {"id": 2}]
    request = {"url": "https://example.com/users?id__in={1, 2}"}
    assert face.get(request) == [{"id": 1}, {"id": 2}]
    request = {"url": "https://example.com/users?id__in=[1, 2]"}
    assert face.get(request) == [{"id": 1}, {"id": 2}]


def test_children(face, items_with_children):
    request = {"url": "https://example.com/users/1/posts"}
    assert face.get(request) == [{"id": 1, "user_id": 1}, {"id": 3, "user_id": 1}]


def test_children_custom(face, items_with_children):
    request = {"url": "https://example.com/users/1/posts?id__lt=2"}
    assert face.get(request) == [{"id": 1, "user_id": 1}]


def test_sort(face, items_unsorted):
    request = {"url": "https://example.com/users?order_by=id"}
    assert face.get(request) == [{"id": i} for i in sorted([21, 3, 19, 37, 28])]


def test_sort_desc(face, items_unsorted):
    request = {"url": "https://example.com/users?order_by=id&desc"}
    assert face.get(request) == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28], reverse=True)
    ]
    request = {"url": "https://example.com/users?desc"}
    assert face.get(request) == [
        {"id": i} for i in sorted([21, 3, 19, 37, 28], reverse=True)
    ]


def test_sort_blank(face, items_unsorted):
    request = {"url": "https://example.com/users"}
    assert face.get(request) == [{"id": i} for i in sorted([21, 3, 19, 37, 28])]


def test_blank_param(face):
    for i in range(1, 5):
        url = "https://example.com/users"
        if i % 2:
            url += f"?is_odd={'true' if i % 3 else 'false'}"
        face.post({"url": url})
    request = {"url": "https://example.com/users?is_odd"}
    assert face.get(request) == [{"id": 1, "is_odd": True}, {"id": 3, "is_odd": False}]


def test_blank_param_no_field(face):
    for i in range(1, 5):
        url = "https://example.com/users"
        if i % 2:
            url += "?is_odd=true"
        face.post({"url": url})
    request = {"url": "https://example.com/users?is_odd"}
    assert face.get(request) == [{"id": 1, "is_odd": True}, {"id": 3, "is_odd": True}]


def test_sort_none(face):
    for i in range(1, 5):
        url = f"https://example.com/users?noneable={i if i % 2 else 'null'}"
        face.post({"url": url})
    request = {"url": "https://example.com/users?order_by=noneable"}
    assert face.get(request) == [
        {"id": 2, "noneable": None},
        {"id": 4, "noneable": None},
        {"id": 1, "noneable": 1},
        {"id": 3, "noneable": 3},
    ]


def test_sort_multiple(face):
    for a in range(2):
        for b in range(2):
            face.post({"url": f"https://example.com/users?a={1 - a}&b={1 - b}"})
            face.post({"url": f"https://example.com/users?a={1 - a}&b={1 - b}"})
    request = {"url": "https://example.com/users?order_by=a,b"}
    assert face.get(request) == [
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
    request = {"url": "https://example.com/users?offset=1"}
    assert face.get(request) == [{"id": i} for i in range(2, 5)]


def test_offset_limit(face, items):
    request = {"url": "https://example.com/users?offset=1&limit=2"}
    assert face.get(request) == [{"id": i} for i in range(2, 4)]


def test_only_names(face):
    request = {"url": "https://example.com/users/posts"}
    assert face.get(request) == []


def test_only_ids(face):
    request = {"url": "https://example.com/1/2"}
    with pytest.raises(NotFound):
        face.get(request)


def test_nonexisting(face):
    request = {"url": "https://example.com/users/1"}
    with pytest.raises(NotFound):
        face.get(request)
