def test_delete_one_existing(face):
    request = {"url": "https://example.com/users/1"}
    assert face.post(request) == 1
    face.delete(request)
    assert face.all() == {"users": []}


def test_delete_one_nonexisting(face):
    request = {"url": "https://example.com/users/1"}
    assert face.post(request) == 1
    face.delete(request)
    face.delete(request)
    assert face.all() == {"users": []}


def test_delete_all_existing(face):
    request = {"url": "https://example.com/users"}
    assert face.post(request) == 1
    face.delete(request)
    assert face.all() == {}


def test_delete_all_nonexisting(face):
    request = {"url": "https://example.com/users"}
    assert face.post(request) == 1
    face.delete(request)
    face.delete(request)
    assert face.all() == {}


def test_delete_one_where_cond(face):
    request = {"url": "https://example.com/users?name=myname"}
    assert face.post(request) == 1
    face.delete(request)
    assert face.all() == {"users": []}
