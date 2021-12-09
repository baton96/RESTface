import pytest

from RESTface import post, put, is_valid_uuid


@pytest.fixture
def root():
    return {}


def test_simple_no_id(root):
    request = {'url': 'https://example.com/users'}
    assert post(request, root) == {'id': 1}
    assert root == {'users': {1: {'id': 1}}}


def test_simple_int_id(root):
    assert post({'url': 'https://example.com/users/1'}, root) == {'id': 1}
    assert root == {'users': {1: {'id': 1}}}
    assert post({'url': 'https://example.com/users'}, root) == {'id': 2}
    assert root == {'users': {1: {'id': 1}, 2: {'id': 2}}}


def test_simple_uuid(root):
    uuid_id = '7189100e-3a2f-4eec-842d-c3f3bc799906'
    request = {'url': f'https://example.com/users/{uuid_id}'}
    assert post(request, root) == {'id': uuid_id}
    assert root == {'users': {uuid_id: {'id': uuid_id}}}
    new_user = post({'url': 'https://example.com/users'}, root)
    assert is_valid_uuid(new_user['id'])
    assert root == {
        'users': {
            uuid_id: {'id': uuid_id},
            new_user['id']: new_user
        }
    }


def test_simple_child(root):
    request = {'url': 'https://example.com/users/1/posts/2'}
    post(request, root)
    assert root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}}
    }


def test_simple_deep(root):
    request = {'url': 'https://example.com/users/1/posts/2/comments/3'}
    post(request, root)
    assert root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1}},
        'comments': {3: {'id': 3, 'post_id': 2}},
    }


def test_simple_url_data(root):
    request = {'url': 'https://example.com/users?name=myname'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'name': 'myname'}}}


def test_simple_body_data(root):
    request = {'url': 'https://example.com/users', 'body': {'name': 'myname'}}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'name': 'myname'}}}


def test_child_url_data(root):
    request = {'url': 'https://example.com/users/1/posts/2?name=myname'}
    post(request, root)
    assert root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1, 'name': 'myname'}},
    }


def test_child_body_data(root):
    request = {'url': 'https://example.com/users/1/posts/2', 'body': {'name': 'myname'}}
    post(request, root)
    assert root == {
        'users': {1: {'id': 1}},
        'posts': {2: {'id': 2, 'user_id': 1, 'name': 'myname'}},
    }


def test_modify_put(root):
    request = {'url': 'https://example.com/users/1?a=b'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'b'}}}
    request = {'url': 'https://example.com/users/1?c=d'}
    put(request, root)
    assert root == {'users': {1: {'id': 1, 'c': 'd'}}}


def test_modify_post(root):
    request = {'url': 'https://example.com/users/1?a=b'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'b'}}}
    request = {'url': 'https://example.com/users/1?c=d'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'b', 'c': 'd'}}}


def test_param_types(root):
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
    post(request, root)
    assert root['users'][1] == {
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


# TODO
'''
def test_same_params(root):
    request = {'url': 'https://example.com/users/1?a=b&a=c'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'b'}}}
'''


def test_only_names(root):
    request = {'url': 'https://example.com/users/posts'}
    assert post(request, root) == {'id': 1}
    assert root == {'users': {}, 'posts': {1: {'id': 1}}}


def test_only_ids(root):
    request = {'url': 'https://example.com/1/2'}
    with pytest.raises(Exception):
        post(request, root)
