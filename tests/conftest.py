import pytest

import RESTface


@pytest.fixture(autouse=True, params=['memory'])
def face(request):
    _face = RESTface.RESTface(request.param)
    yield _face
    _face.reset()
