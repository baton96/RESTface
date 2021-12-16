import storage
import pytest

storage_type = 'memory'


@pytest.fixture(autouse=True)
def reset():
    if storage_type == 'memory':
        storage.root = {}
    elif storage_type == 'db':
        for table in storage.db.tables:
            storage.db[table].drop()


def get_items():
    if storage_type == 'memory':
        return storage.root
    elif storage_type == 'db':
        return {table: {row['id']: row for row in storage.db[table].all()} for table in storage.db.tables}
