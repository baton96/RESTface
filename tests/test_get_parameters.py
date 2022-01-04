import pytest


@pytest.fixture
def items(face):
    for i in range(5):
        request = {'url': f'https://example.com/users'}
        face.post(request)


@pytest.fixture
def items_strings(face):
    for char in ['a', 'b']:
        request = {'url': f'https://example.com/users?char={char}'}
        face.post(request)


def test_eq(face, items):
    request = {'url': 'https://example.com/users?id=1'}
    assert face.get(request) == [{'id': 1}]


def test_lte(face, items):
    request = {'url': 'https://example.com/users?id__lte=2'}
    assert face.get(request) == [{'id': 1}, {'id': 2}]


def test_lt(face, items):
    request = {'url': 'https://example.com/users?id__lt=4'}
    assert face.get(request) == [{'id': 1}, {'id': 2}, {'id': 3}]


def test_gte(face, items):
    request = {'url': 'https://example.com/users?id__gte=3'}
    assert face.get(request) == [{'id': 3}, {'id': 4}, {'id': 5}]


def test_gt(face, items):
    request = {'url': 'https://example.com/users?id__gt=3'}
    assert face.get(request) == [{'id': 4}, {'id': 5}]


def test_between(face, items):
    request = {'url': 'https://example.com/users?id__between=2,4'}
    assert face.get(request) == [{'id': 2}, {'id': 3}, {'id': 4}]


def test_in(face, items):
    request = {'url': 'https://example.com/users?id__in=2,4'}
    assert face.get(request) == [{'id': 2}, {'id': 4}]


def test_notin(face, items):
    request = {'url': 'https://example.com/users?id__notin=2,3,4'}
    assert face.get(request) == [{'id': 1}, {'id': 5}]


def test_ilike(face, items_strings):
    request = {'url': 'https://example.com/users?char__ilike=a'}
    assert face.get(request) == [{'id': 1, 'char': 'a'}]


def test_like(face, items_strings):
    request = {'url': 'https://example.com/users?char__like=b'}
    assert face.get(request) == [{'id': 2, 'char': 'b'}]


def test_startswith(face, items_strings):
    request = {'url': 'https://example.com/users?char__startswith=a'}
    assert face.get(request) == [{'id': 1, 'char': 'a'}]


def test_endswith(face, items_strings):
    request = {'url': 'https://example.com/users?char__endswith=b'}
    assert face.get(request) == [{'id': 2, 'char': 'b'}]
