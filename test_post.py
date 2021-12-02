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


def test_modify(root):
    request = {'url': 'https://example.com/users/1?a=b'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'b'}}}
    request = {'url': 'https://example.com/users/1?a=c'}
    post(request, root)
    assert root == {'users': {1: {'id': 1, 'a': 'c'}}}


def test_param_types_bool(root):
    request = {'url': 'https://example.com/users?big_true=True&small_true=true&big_false=False&small_false=false'}
    post(request, root)
    assert root['users'][1] == {
        'id': 1,
        'big_true': True,
        'small_true': True,
        'big_false': False,
        'small_false': False
    }


def test_param_types_none(root):
    request = {'url': 'https://example.com/users?none=none&null=null'}
    post(request, root)
    assert root['users'][1] == {
        'id': 1,
        'none': None,
        'null': None
    }
