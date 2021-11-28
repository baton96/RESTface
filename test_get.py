import pytest

from RESTface import get, post


@pytest.fixture
def root():
    _root = {}
    for i in range(1, 5):
        request = {'url': f'https://example.com/users'}
        post(request, _root)
    return _root


@pytest.fixture
def root_children():
    _root_children = {}
    for i in range(4):
        request = {'url': f'https://example.com/users/{(i % 2) + 1}/posts'}
        post(request, _root_children)
    return _root_children


def test_get_all(root):
    request = {'url': 'https://example.com/users'}
    assert get(request, root) == [{'id': i} for i in range(1, 5)]


def test_get_by_id(root):
    request = {'url': 'https://example.com/users/1'}
    assert get(request, root) == [{'id': 1}]
    request = {'url': 'https://example.com/users?id=1'}
    assert get(request, root) == [{'id': 1}]
    request = {'url': 'https://example.com/users?id__eq=1'}
    assert get(request, root) == [{'id': 1}]


def test_lte(root):
    request = {'url': 'https://example.com/users?id__lt=3'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__le=2'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__lte=2'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]


def test_in(root):
    request = {'url': 'https://example.com/users?id__in=(1,2)'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__in={1, 2}'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]
    request = {'url': 'https://example.com/users?id__in=[1, 2]'}
    assert get(request, root) == [{'id': 1}, {'id': 2}]


def test_children(root_children):
    request = {'url': 'https://example.com/users/1/posts'}
    assert get(request, root_children) == [{'id': 1, 'user_id': 1}, {'id': 3, 'user_id': 1}]


def test_children_custom(root_children):
    request = {'url': 'https://example.com/users/1/posts?id__lt=2'}
    assert get(request, root_children) == [{'id': 1, 'user_id': 1}]
