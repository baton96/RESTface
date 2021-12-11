import RESTface
import pytest


@pytest.fixture(autouse=True)
def reset():
    if RESTface.storage_type == 'memory':
        RESTface.root = {}
    elif RESTface.storage_type == 'db':
        for table in RESTface.db.tables:
            RESTface.db[table].drop()


def get_items():
    if RESTface.storage_type == 'memory':
        return RESTface.root
    elif RESTface.storage_type == 'db':
        return {table: {row['id']: row for row in RESTface.db[table].all()} for table in RESTface.db.tables}

