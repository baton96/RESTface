from conftest import get_items, post
import pytest


def test_simple_no_id():
    request = {'url': 'https://example.com/users'}
    assert post(request) == 1
    assert get_items() == {'users': {1: {'id': 1}}}


def test_simple_int_id():
    assert post({'url': 'https://example.com/users/1'}) == 1
    assert get_items() == {'users': {1: {'id': 1}}}
    assert post({'url': 'https://example.com/users'}) == 2
    assert get_items() == {'users': {1: {'id': 1}, 2: {'id': 2}}}


def test_simple_child_no_id():
    request = {'url': 'https://example.com/users/1/posts'}
    post(request)
    assert get_items() == {
        'users': {1: {'id': 1}},
        'posts': {1: {'id': 1, 'user_id': 1}}
    }


def test_simple_child_id():
    request = {'url': 'https://example.com/users/1/posts/2'}
    post(request)
    assert get_items() == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}}
    }


def test_simple_deep():
    request = {'url': 'https://example.com/users/1/posts/2/comments/3'}
    post(request)
    assert get_items() == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}},
        'comments': {3: {'id': 3, 'post_id': 2}},
    }


def test_simple_url_data():
    request = {'url': 'https://example.com/users?name=myname'}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'name': 'myname'}}}


def test_simple_body_data():
    request = {'url': 'https://example.com/users', 'body': {'name': 'myname'}}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'name': 'myname'}}}


def test_child_url_data():
    request = {'url': 'https://example.com/users/1/posts/2?name=myname'}
    post(request)
    assert get_items() == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1, 'name': 'myname'}},
    }


def test_child_body_data():
    request = {'url': 'https://example.com/users/1/posts/2', 'body': {'name': 'myname'}}
    post(request)
    assert get_items() == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1, 'name': 'myname'}},
    }


@pytest.mark.skip
def test_modify_put():
    request = {'url': 'https://example.com/users/1?a=b'}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'a': 'b'}}}
    request = {'url': 'https://example.com/users/1?c=d'}
    put(request)
    assert get_items() == {'users': {1: {'id': 1, 'c': 'd'}}}


def test_modify_post():
    request = {'url': 'https://example.com/users/1?a=b'}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'a': 'b'}}}
    request = {'url': 'https://example.com/users/1?c=d'}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'a': 'b', 'c': 'd'}}}


def test_param_types():
    params = {
        'int': '1',
        'float': '0.5',
        'str': 'value',
        'big_true': 'True',
        'small_true': 'true',
        'big_false': 'False',
        'small_false': 'false',
        'none': 'none',
        'null': 'null',
        'empty': ''
    }
    params = '&'.join(f'{name}={value}' for name, value in params.items())
    request = {'url': f'https://example.com/users?{params}'}
    post(request)
    assert get_items()['users'][1] == {
        'id': 1,
        'int': 1,
        'float': 0.5,
        'str': 'value',
        'big_true': True,
        'small_true': True,
        'big_false': False,
        'small_false': False,
        'none': None,
        'null': None,
        'empty': ''
    }


@pytest.mark.skip
def test_same_params():
    request = {'url': 'https://example.com/users/1?a=b&a=c'}
    post(request)
    assert get_items() == {'users': {1: {'id': 1, 'a': 'b'}}}


def test_only_names():
    request = {'url': 'https://example.com/users/posts'}
    assert post(request) == 1
    assert get_items() == {'users': {}, 'posts': {1: {'id': 1}}}


def test_only_ids():
    request = {'url': 'https://example.com/1/2'}
    with pytest.raises(Exception):
        post(request)
