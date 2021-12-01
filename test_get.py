import pytest

from RESTface import get, post


@pytest.fixture
def empty_root():
    return {}


@pytest.fixture
def root():
    _root = {}
    for i in range(1, 5):
        request = {'url': f'https://example.com/users'}
        post(request, _root)
    return _root


@pytest.fixture
def root_children():
    _root = {}
    for i in range(4):
        request = {'url': f'https://example.com/users/{(i % 2) + 1}/posts'}
        post(request, _root)
    return _root


@pytest.fixture
def root_unsorted():
    _root = {}
    for i in [21, 3, 19, 37, 28]:
        request = {'url': f'https://example.com/users/{i}'}
        post(request, _root)
    return _root


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


def test_simple_no_id(empty_root):
    request = {'url': 'https://example.com/users'}
    assert get(request, empty_root) == []
    assert empty_root == {'users': {}}


def test_simple_id(empty_root):
    request = {'url': 'https://example.com/users/1'}
    assert get(request, empty_root) == [{'id': 1}]
    assert empty_root == {'users': {1: {'id': 1}}}


def test_simple_child(empty_root):
    request = {'url': 'https://example.com/users/1/posts/2'}
    assert get(request, empty_root) == [{'id': 2, 'user_id': 1}]
    assert empty_root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}}
    }


def test_simple_deep(empty_root):
    request = {'url': 'https://example.com/users/1/posts/2/comments/3'}
    assert get(request, empty_root) == [{'id': 3, 'post_id': 2}]
    assert empty_root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}},
        'comments': {3: {'id': 3, 'post_id': 2}},
    }


def test_sort(root_unsorted):
    request = {'url': 'https://example.com/users?sort=id'}
    assert get(request, root_unsorted) == [{'id': i} for i in sorted([21, 3, 19, 37, 28])]


def test_sort_desc(root_unsorted):
    request = {'url': 'https://example.com/users?sort=id&desc'}
    assert get(request, root_unsorted) == [{'id': i} for i in sorted([21, 3, 19, 37, 28], reverse=True)]


def test_blank_param(empty_root):
    for i in range(1, 5):
        url = f'https://example.com/users?is_odd={i % 2}'
        post({'url': url}, empty_root)
    request = {'url': 'https://example.com/users?is_odd'}
    assert get(request, empty_root) == [{'id': 1, 'is_odd': True}, {'id': 3, 'is_odd': True}]


def test_blank_param_no_field(empty_root):
    for i in range(1, 5):
        url = f'https://example.com/users'
        if i % 2:
            url += '?is_odd=true'
        post({'url': url}, empty_root)
    request = {'url': 'https://example.com/users?is_odd'}
    assert get(request, empty_root) == [{'id': 1, 'is_odd': True}, {'id': 3, 'is_odd': True}]
