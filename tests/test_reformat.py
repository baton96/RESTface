import pytest
from inflect import engine as get_engine

from utils import (
    to_yaml,
    to_xml,
    to_csv,
    from_yaml,
    from_xml,
    from_csv,
)

engine = get_engine()
test_objects = [[{"a": "b"}, {"c": "d"}], {"a": {"b": "c"}}, {"a": ["b", "c"]}]


@pytest.fixture()
def face():
    return


@pytest.mark.parametrize("test_obj", test_objects)
def test_yaml(test_obj):
    assert from_yaml(to_yaml(test_obj)) == test_obj


@pytest.mark.parametrize("test_obj", test_objects)
def test_xml(test_obj):
    assert from_xml(to_xml(test_obj, "users")) == test_obj


@pytest.mark.parametrize("test_obj", test_objects[:-1])
def test_csv(test_obj):
    assert from_csv(to_csv(test_obj)) == test_obj
