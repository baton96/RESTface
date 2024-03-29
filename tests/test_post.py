import uuid
import warnings

import pytest


def is_valid_uuid(element):
    try:
        uuid.UUID(element)
        return True
    except (ValueError, AttributeError):
        return False


def test_simple_no_id(face):
    request = {'url': 'https://example.com/users'}
    assert face.post(request) == 1
    assert face.all() == {'users': [{'id': 1}]}


def test_simple_int_id(face):
    assert face.post({'url': 'https://example.com/users/1'}) == 1
    assert face.all() == {'users': [{'id': 1}]}
    assert face.post({'url': 'https://example.com/users'}) == 2
    assert face.all() == {'users': [{'id': 1}, {'id': 2}]}


def test_simple_uuid_id(face):
    face.storage = face.storage.__class__(uuid_id=True)
    item_id = str(uuid.uuid4())
    assert face.post({'url': f'https://example.com/users/{item_id}'}) == item_id
    assert face.all() == {'users': [{'id': item_id}]}
    new_item_id = face.post({'url': 'https://example.com/users'})
    assert is_valid_uuid(new_item_id)
    assert sorted(
        face.all()['users'],
        key=lambda item: item['id']
    ) == sorted(
        [{'id': item_id}, {'id': new_item_id}],
        key=lambda item: item['id']
    )


def test_simple_child_no_id(face):
    request = {'url': 'https://example.com/users/1/posts'}
    face.post(request)
    assert face.all() == {
        'users': [{'id': 1}],
        'posts': [{'id': 1, 'user_id': 1}]
    }


def test_simple_child_id(face):
    request = {'url': 'https://example.com/users/1/posts/2'}
    face.post(request)
    assert face.all() == {
        'users': [{'id': 1}],
        'posts': [{'id': 2, 'user_id': 1}]
    }


def test_simple_deep(face):
    request = {'url': 'https://example.com/users/1/posts/2/comments/3'}
    face.post(request)
    assert face.all() == {
        'users': [{'id': 1}],
        'posts': [{'id': 2, 'user_id': 1}],
        'comments': [{'id': 3, 'post_id': 2}],
    }


def test_simple_url_data(face):
    request = {'url': 'https://example.com/users?name=myname'}
    face.post(request)
    assert face.all() == {'users': [{'id': 1, 'name': 'myname'}]}


def test_simple_body_data(face):
    request = {'url': 'https://example.com/users', 'body': {'name': 'myname'}}
    face.post(request)
    assert face.all() == {'users': [{'id': 1, 'name': 'myname'}]}


def test_child_url_data(face):
    request = {'url': 'https://example.com/users/1/posts/2?name=myname'}
    face.post(request)
    assert face.all() == {
        'users': [{'id': 1}],
        'posts': [{'id': 2, 'user_id': 1, 'name': 'myname'}],
    }


def test_child_body_data(face):
    request = {'url': 'https://example.com/users/1/posts/2', 'body': {'name': 'myname'}}
    face.post(request)
    assert face.all() == {
        'users': [{'id': 1}],
        'posts': [{'id': 2, 'user_id': 1, 'name': 'myname'}],
    }


def test_modify_post(face):
    request = {'url': 'https://example.com/users/1?a=b'}
    face.post(request)
    assert face.all() == {'users': [{'id': 1, 'a': 'b'}]}
    request = {'url': 'https://example.com/users/1?c=d'}
    face.post(request)
    assert face.all() == {'users': [{'id': 1, 'a': 'b', 'c': 'd'}]}


def test_modify_put(face):
    if face.storage.__class__.__name__ == 'DbStorage':
        warnings.warn('PUT method is not implemented for DbStorage')
        return

    request = {'url': 'https://example.com/users/1?a=b'}
    face.put(request)
    assert face.all() == {'users': [{'id': 1, 'a': 'b'}]}
    request = {'url': 'https://example.com/users/1?c=d'}
    face.put(request)
    assert face.all() == {'users': [{'id': 1, 'c': 'd'}]}


def test_param_types(face):
    params = {
        'int': '1',
        'float': '0.5',
        'str': 'value',
        'true': 'true',
        'false': 'false',
        'null': 'null',
        'empty': ''
    }
    params = '&'.join(f'{name}={value}' for name, value in params.items())
    request = {'url': f'https://example.com/users?{params}'}
    face.post(request)
    assert face.all()['users'][0] == {
        'id': 1,
        'int': 1,
        'float': 0.5,
        'str': 'value',
        'true': True,
        'false': False,
        'null': None,
        'empty': ''
    }


@pytest.mark.skip
def test_same_params(face):
    request = {'url': 'https://example.com/users/1?a=b&a=c'}
    face.post(request)
    assert face.all() == {'users': [{'id': 1, 'a': 'b'}]}


def test_only_names(face):
    request = {'url': 'https://example.com/users/posts'}
    assert face.post(request) == 1
    assert face.all() == {'posts': [{'id': 1}]}


def test_only_ids(face):
    request = {'url': 'https://example.com/1/2'}
    with pytest.raises(Exception):
        face.post(request)


def test_bulk(face):
    request = {'url': 'https://example.com/users', 'body': [{'name': 'a'}, {'name': 'b'}]}
    assert face.post(request) == [1, 2]
    assert face.all() == {'users': [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]}


def test_bulk_existing(face):
    request = {'url': 'https://example.com/users', 'body': [{'name': 'a'}, {'name': 'b'}]}
    assert face.post(request) == [1, 2]
    request = {'url': 'https://example.com/users', 'body': [{'id': 1, 'name': 'c'}, {'id': 2, 'name': 'd'}]}
    assert face.post(request) == [1, 2]
    assert face.all() == {'users': [{'id': 1, 'name': 'c'}, {'id': 2, 'name': 'd'}]}


def test_bulk_partially_existing(face):
    request = {'url': 'https://example.com/users', 'body': [{'name': 'a'}, {'name': 'b'}]}
    assert face.post(request) == [1, 2]
    request = {'url': 'https://example.com/users', 'body': [{'id': 1, 'name': 'c'}, {'name': 'd'}]}
    assert face.post(request) == [1, 3]
    assert face.all() == {'users': [{'id': 1, 'name': 'c'}, {'id': 2, 'name': 'b'}, {'id': 3, 'name': 'd'}]}
