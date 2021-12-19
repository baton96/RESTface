import pytest

import RESTface
from storage import DbStorage, MemoryStorage, FileStorage

storage_type = 'file'
face = RESTface.RESTface(storage_type)
get, post, delete = face.get, face.post, face.delete


@pytest.fixture(autouse=True)
def reset():
    if storage_type == 'memory':
        MemoryStorage.root = {}
    elif storage_type == 'db':
        for table in DbStorage.db.tables:
            DbStorage.db[table].drop()
    elif storage_type == 'file':
        FileStorage.db.drop_tables()


def get_items():
    if storage_type == 'memory':
        return MemoryStorage.root
    elif storage_type == 'db':
        return {table: {row['id']: row for row in DbStorage.db[table].all()} for table in DbStorage.db.tables}
    elif storage_type == 'file':
        return {table: {row.get('id'): row for row in FileStorage.db.table(table).all()} for table in FileStorage.db.tables()}
