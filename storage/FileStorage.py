from typing import Union

import tinydb

from .JSONStorage import JSONStorage


class FileStorage(JSONStorage):
    def __init__(self, storage_path: str = None, uuid_id: bool = False):
        super().__init__(storage_path, uuid_id)
        if storage_path:
            self.db = tinydb.TinyDB(storage_path)
        else:
            self.db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)

    def get_with_id(self, table_name: str, item_id: Union[int, str]) -> dict:
        table = self.get_table(table_name)
        return table.get(doc_id=item_id) or {}

    def put_n_post(self, table_name: str, data: dict, method: str = 'POST') -> Union[int, str]:
        table = self.get_table(table_name)
        item_id = self.get_id(table_name, data)
        data['id'] = item_id
        return table.upsert(tinydb.table.Document(data, doc_id=item_id))[0]

    def delete(self, table_name: str, item_id: Union[int, str] = None) -> bool:
        if item_id:
            table = self.get_table(table_name)
            try:
                table.remove(doc_ids=[item_id])
                return True
            except KeyError:
                return False
        else:
            existed = table_name in self.db.tables()
            self.db.drop_table(table_name)
            return existed

    def all(self) -> dict:
        return {
            table_name: self.get_table(table_name).all()
            for table_name in self.db.tables()
        }

    def reset(self) -> None:
        self.db.drop_tables()

    def get_table(self, table_name):
        table = self.db.table(table_name)
        table.document_id_class = self.primary_type
        return table

    def get_items(self, table_name: str):
        return self.get_table(table_name).all()
