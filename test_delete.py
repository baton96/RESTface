from RESTface import storage_type, post, delete
import RESTface
import pytest


def get_all_rows():
    return {table: {row['id']: row for row in RESTface.db[table].all()} for table in RESTface.db.tables}


@pytest.fixture
def get_items():
    if storage_type == 'memory':
        return lambda: RESTface.root
    elif storage_type == 'db':
        return lambda: get_all_rows()


def test_delete_one_existing(get_items):
    request = {'url': 'https://example.com/users/1'}
    assert post(request) == 1
    delete(request)
    assert get_items() == {'users': {}}


def test_delete_one_nonexisting(get_items):
    request = {'url': 'https://example.com/users/1'}
    assert post(request) == 1
    delete(request)
    delete(request)
    assert get_items() == {'users': {}}


def test_delete_all_existing(get_items):
    request = {'url': 'https://example.com/users'}
    assert post(request) == 1
    delete(request)
    assert get_items() == {}


def test_delete_all_nonexisting(get_items):
    request = {'url': 'https://example.com/users'}
    assert post(request) == 1
    delete(request)
    delete(request)
    assert get_items() == {}
