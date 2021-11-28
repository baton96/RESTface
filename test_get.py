import pytest

from restface import get, post


@pytest.fixture
def root():
    _root = {}
    for i in range(1, 10):
        request = {'url': f'https://example.com/users'}
        post(request, _root)
    return _root


def test_get_all(root):
    request = {'url': 'https://example.com/users'}
    assert get(request, root) == [{'id': i} for i in range(1, 10)]


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
