import uuid

import dataset


class DbStorage:
    def __init__(self, storage_path: str = "sqlite:///:memory:", uuid_id: bool = False):
        self.db = dataset.connect(storage_path, row_type=dict)
        self.primary_type = self.db.types.string if uuid_id else self.db.types.integer

    def get_with_id(self, table_name: str, item_id: int | str) -> dict:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        return table.find_one(id=item_id) or {}

    def get_without_id(
        self, table_name: str, where_params: list, meta_params: dict
    ) -> list:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        where_params = {
            param_name: ({op_name: param_value} if param_value else {"not": None})
            for op_name, param_name, param_value in where_params
        }
        if meta_params.pop("desc", False):
            meta_params["order_by"] = [
                "-" + order_by_arg.lstrip("-")
                for order_by_arg in meta_params["order_by"]
            ]
        if not meta_params["_limit"]:
            meta_params.pop("_limit", None)
        params = {**where_params, **meta_params}
        items = list(table.find(**params))
        return items

    def put_n_post(
        self, table_name: str, data: dict, method: str = "POST"
    ) -> int | str:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        if "id" not in data and self.primary_type == self.db.types.string:
            data["id"] = str(uuid.uuid4())
        if method == "PUT":
            table.delete(id=data.get("id"))
        item_id = table.upsert(data, ["id"], ensure=True)
        if item_id is True:
            item_id = data["id"]
        return item_id

    def bulk_put_n_post(
        self, table_name: str, items: list[dict], method: str = "POST"
    ) -> list[int | str]:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        if self.primary_type is self.db.types.string:
            for item in items:
                item.setdefault("id", str(uuid.uuid4()))
        if method == "PUT":
            item_ids = [item["id"] for item in items if "id" in items]
            table.delete(id={"in": item_ids})
        upserted_ids = [table.upsert(item, ["id"], ensure=True) for item in items]
        item_ids = [item.get("id") for item in items]
        return [
            item_id if upserted_id is True else upserted_id
            for upserted_id, item_id in zip(upserted_ids, item_ids)
        ]

    def delete(
        self, table_name: str, where_params: list, item_id: int | str = None
    ) -> None:
        table = self.db.get_table(table_name, primary_type=self.primary_type)
        if not item_id:
            table.drop()
        else:
            where_params = {
                param_name: ({op_name: param_value} if param_value else {"not": None})
                for op_name, param_name, param_value in where_params
            }
            table.delete(**where_params)

    def all(self) -> dict:
        return {
            table_name: list(self.db[table_name].all()) for table_name in self.db.tables
        }

    def reset(self) -> None:
        for table in self.db.tables:
            self.db[table].drop()
