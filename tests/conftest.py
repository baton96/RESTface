import pytest

import RESTface


@pytest.fixture(
    autouse=True,
    params=[
        "memory",
        "file",
        "db",
        # 'mongo',
        # 'redis'
    ],
)
def face(request):
    _face = RESTface.RESTface(request.param)
    yield _face
    _face.reset()
