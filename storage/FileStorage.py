import tinydb

from .BaseStorage import BaseStorage


class FileStorage(BaseStorage):
    def __init__(self, storage_path: str | None = None, uuid_id: bool = False):
        super().__init__(storage_path, uuid_id)
        if storage_path:
            self.db = tinydb.TinyDB(storage_path)
        else:
            self.db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)

    def get_with_id(self, table_name: str, item_id: int | str) -> dict:
        table = self.get_table(table_name)
        return table.get(doc_id=item_id)

    def upsert(self, table_name: str, data: dict, method: str = "POST") -> int | str:
        item_id = self.get_id(table_name, data)
        table = self.get_table(table_name)
        if method == "PUT":
            try:
                table.remove(doc_ids=[item_id])
            except KeyError:
                ...
        table.upsert(tinydb.table.Document(data, doc_id=item_id))  # type: ignore[arg-type]
        return item_id

    def bulk_upsert(
        self, table_name: str, items: list[dict], method: str = "POST"
    ) -> list[int | str]:
        table = self.get_table(table_name)
        self.bulk_get_ids(table_name, items)
        item_ids = set(self.get_ids(table_name))
        table.update_multiple(
            [
                (item, tinydb.where("id") == item["id"])
                for item in items
                if item["id"] in item_ids
            ]
        )
        table.insert_multiple(
            [
                tinydb.table.Document(item, doc_id=item["id"])
                for item in items
                if item["id"] not in item_ids
            ]
        )
        return [item["id"] for item in items]

    def delete_with_id(self, table_name: str, doc_id: int | str) -> bool:
        table = self.get_table(table_name)
        try:
            return bool(table.remove(doc_ids=[doc_id]))
        except KeyError:
            return False

    def delete_without_id(self, table_name: str, where_params: list) -> None:
        if where_params:
            doc_ids = [
                item["id"]
                for item in self.get_table(table_name).all()
                if all(self.fulfill_cond(item, param) for param in where_params)
            ]
            self.get_table(table_name).remove(doc_ids=doc_ids)
        else:
            self.db.drop_table(table_name)

    def all(self) -> dict:
        return {
            table_name: self.get_table(table_name).all()
            for table_name in self.db.tables()
        }

    def reset(self) -> None:
        self.db.drop_tables()

    def get_ids(self, table_name: str) -> list[int | str]:
        return [item["id"] for item in self.get_table(table_name).all()]

    def get_table(self, table_name):
        table = self.db.table(table_name)
        table.document_id_class = self.primary_type
        return table

    def get_items(self, table_name: str) -> list[dict]:
        return self.get_table(table_name).all()
