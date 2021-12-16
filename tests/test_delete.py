from RESTface import post, delete
from conftest import get_items


def test_delete_one_existing():
    request = {'url': 'https://example.com/users/1'}
    assert post(request) == 1
    delete(request)
    assert get_items() == {'users': {}}


def test_delete_one_nonexisting():
    request = {'url': 'https://example.com/users/1'}
    assert post(request) == 1
    delete(request)
    delete(request)
    assert get_items() == {'users': {}}


def test_delete_all_existing():
    request = {'url': 'https://example.com/users'}
    assert post(request) == 1
    delete(request)
    assert get_items() == {}


def test_delete_all_nonexisting():
    request = {'url': 'https://example.com/users'}
    assert post(request) == 1
    delete(request)
    delete(request)
    assert get_items() == {}
