import pytest

from RESTface import post, delete


@pytest.fixture
def root():
    return {}


def test_delete_one_existing(root):
    request = {'url': 'https://example.com/users/1'}
    assert post(request, root) == {'id': 1}
    delete(request, root)
    assert root == {'users': {}}


def test_delete_one_nonexisting(root):
    request = {'url': 'https://example.com/users/1'}
    assert post(request, root) == {'id': 1}
    delete(request, root)
    delete(request, root)
    assert root == {'users': {}}


def test_delete_all_existing(root):
    request = {'url': 'https://example.com/users'}
    assert post(request, root) == {'id': 1}
    delete(request, root)
    assert root == {}


def test_delete_all_nonexisting(root):
    request = {'url': 'https://example.com/users'}
    assert post(request, root) == {'id': 1}
    delete(request, root)
    delete(request, root)
    assert root == {}
