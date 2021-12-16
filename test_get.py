import pytest

from RESTface import get, post


@pytest.fixture
def items():
    for i in range(1, 5):
        request = {'url': f'https://example.com/users'}
        post(request)


@pytest.fixture
def items_with_children():
    for i in range(4):
        request = {'url': f'https://example.com/users/{(i % 2) + 1}/posts'}
        post(request)


@pytest.fixture
def items_unsorted():
    for i in [21, 3, 19, 37, 28]:
        request = {'url': f'https://example.com/users/{i}'}
        post(request)


def test_get_all(items):
    request = {'url': 'https://example.com/users'}
    assert get(request) == [{'id': i} for i in range(1, 5)]


def test_get_by_id(items):
    request = {'url': 'https://example.com/users/1'}
    assert get(request) == {'id': 1}
    request = {'url': 'https://example.com/users?id=1'}
    assert get(request) == [{'id': 1}]


def test_lte(items):
    request = {'url': 'https://example.com/users?id__lt=3'}
    assert get(request) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__lte=2'}
    assert get(request) == [{'id': 1}, {'id': 2}]


def test_in(items):
    request = {'url': 'https://example.com/users?id__in=(1,2)'}
    assert get(request) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__in={1, 2}'}
    assert get(request) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__in=[1, 2]'}
    assert get(request) == [{'id': 1}, {'id': 2}]


def test_children(items_with_children):
    request = {'url': 'https://example.com/users/1/posts'}
    assert get(request) == [{'id': 1, 'user_id': 1}, {'id': 3, 'user_id': 1}]


def test_children_custom(items_with_children):
    request = {'url': 'https://example.com/users/1/posts?id__lt=2'}
    assert get(request) == [{'id': 1, 'user_id': 1}]


def test_sort(items_unsorted):
    request = {'url': 'https://example.com/users?order_by=id'}
    assert get(request) == [{'id': i} for i in sorted([21, 3, 19, 37, 28])]


def test_sort_desc(items_unsorted):
    request = {'url': 'https://example.com/users?order_by=id&desc'}
    assert get(request) == [{'id': i} for i in sorted([21, 3, 19, 37, 28], reverse=True)]
    request = {'url': 'https://example.com/users?desc'}
    assert get(request) == [{'id': i} for i in sorted([21, 3, 19, 37, 28], reverse=True)]


def test_sort_blank(items_unsorted):
    request = {'url': 'https://example.com/users?sort'}
    assert get(request) == [{'id': i} for i in sorted([21, 3, 19, 37, 28])]


def test_blank_param():
    for i in range(1, 5):
        url = 'https://example.com/users'
        if i % 2:
            url += f'?is_odd={bool(i % 3)}'
        post({'url': url})
    request = {'url': 'https://example.com/users?is_odd'}
    assert get(request) == [{'id': 1, 'is_odd': True}, {'id': 3, 'is_odd': False}]


def test_blank_param_no_field():
    for i in range(1, 5):
        url = f'https://example.com/users'
        if i % 2:
            url += '?is_odd=true'
        post({'url': url})
    request = {'url': 'https://example.com/users?is_odd'}
    assert get(request) == [{'id': 1, 'is_odd': True}, {'id': 3, 'is_odd': True}]


def test_sort_none():
    for i in range(1, 5):
        url = f'https://example.com/users?noneable={i if i % 2 else None}'
        post({'url': url})
    request = {'url': 'https://example.com/users?order_by=noneable'}
    assert get(request) == [
        {'id': 2, 'noneable': None},
        {'id': 4, 'noneable': None},
        {'id': 1, 'noneable': 1},
        {'id': 3, 'noneable': 3},
    ]


def test_only_names():
    request = {'url': 'https://example.com/users/posts'}
    assert get(request) == []


def test_only_ids(items):
    request = {'url': 'https://example.com/1/2'}
    assert get(request) == {}
