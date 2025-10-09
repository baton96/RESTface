import pytest


@pytest.fixture
def items(face):
    for i in range(5):
        face.post("https://example.com/users")


@pytest.fixture
def items_strings(face):
    for char in ["a", "b"]:
        face.post(f"https://example.com/users?char={char}")


def test_eq(face, items):
    assert face.get("https://example.com/users?id=1") == [{"id": 1}]


def test_lte(face, items):
    assert face.get("https://example.com/users?id__lte=2") == [{"id": 1}, {"id": 2}]


def test_lt(face, items):
    assert face.get("https://example.com/users?id__lt=4") == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]


def test_gte(face, items):
    assert face.get("https://example.com/users?id__gte=3") == [
        {"id": 3},
        {"id": 4},
        {"id": 5},
    ]


def test_gt(face, items):
    assert face.get("https://example.com/users?id__gt=3") == [{"id": 4}, {"id": 5}]


def test_between(face, items):
    assert face.get("https://example.com/users?id__between=2,4") == [
        {"id": 2},
        {"id": 3},
        {"id": 4},
    ]


def test_in(face, items):
    assert face.get("https://example.com/users?id__in=2,4") == [{"id": 2}, {"id": 4}]


def test_notin(face, items):
    assert face.get("https://example.com/users?id__notin=2,3,4") == [
        {"id": 1},
        {"id": 5},
    ]


def test_ilike(face, items_strings):
    assert face.get("https://example.com/users?char__ilike=a") == [
        {"id": 1, "char": "a"}
    ]


def test_like(face, items_strings):
    assert face.get("https://example.com/users?char__like=b") == [
        {"id": 2, "char": "b"}
    ]


def test_startswith(face, items_strings):
    assert face.get("https://example.com/users?char__startswith=a") == [
        {"id": 1, "char": "a"}
    ]


def test_endswith(face, items_strings):
    assert face.get("https://example.com/users?char__endswith=b") == [
        {"id": 2, "char": "b"}
    ]
