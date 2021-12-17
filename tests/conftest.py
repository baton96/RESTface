from storage import DbStorage, MemoryStorage
import RESTface
import pytest

storage_type = 'db'
face = RESTface.RESTface(storage_type)
get, post, delete = face.get, face.post, face.delete


@pytest.fixture(autouse=True)
def reset():
    if storage_type == 'memory':
        MemoryStorage.root = {}
    elif storage_type == 'db':
        for table in DbStorage.db.tables:
            DbStorage.db[table].drop()


def get_items():
    if storage_type == 'memory':
        return MemoryStorage.root
    elif storage_type == 'db':
        return {table: {row['id']: row for row in DbStorage.db[table].all()} for table in DbStorage.db.tables}
