from typing import Union, List

import pymongo
from pymongo import UpdateOne, ReplaceOne

from .BaseStorage import BaseStorage


class MongoStorage(BaseStorage):
    def __init__(
        self, storage_path: str = "mongodb://localhost:27017", uuid_id: bool = False
    ):
        self.db = pymongo.MongoClient(storage_path).db
        self.primary_type = str if uuid_id else int

    def get_with_id(self, collection_name: str, item_id: Union[int, str]) -> dict:
        collection = self.db[collection_name]
        return {
            (k if k != "_id" else "id"): v
            for k, v in (collection.find_one({"_id": item_id}) or {}).items()
        }

    def get_without_id(
        self, collection_name: str, where_params_raw: list, meta_params: dict
    ) -> list:
        collection = self.db[collection_name]
        where_params = {}
        for op_name, param_name, param_value in where_params_raw:
            if param_name == "id":
                param_name = "_id"

            if op_name == "=":
                if param_value == "":
                    where_params[param_name] = {"$exists": True}
                else:
                    where_params[param_name] = param_value
            elif op_name == "between":
                where_params[param_name] = {
                    "$gte": param_value[0],
                    "$lte": param_value[-1],
                }
            elif op_name == "startswith":
                where_params[param_name] = {"$regex": "^" + param_value}
            elif op_name == "endswith":
                where_params[param_name] = {"$regex": param_value + "$"}
            elif "like" in op_name:
                where_params[param_name] = {"$regex": param_value}
                if op_name[0] == "i":
                    where_params[param_name]["$options"] = "i"
            elif op_name == "notin":
                where_params[param_name] = {"$nin": param_value}
            else:
                where_params[param_name] = {("$" + op_name): param_value}

        desc = meta_params["desc"]
        order_by = meta_params["order_by"]
        order_key = [
            (
                order_by_arg if order_by_arg != "id" else "_id",
                pymongo.DESCENDING if desc else pymongo.ASCENDING,
            )
            for order_by_arg in order_by
        ]
        results = collection.find(
            filter=where_params,
            sort=order_key,
            skip=meta_params["_offset"],
            limit=meta_params["_limit"],
        )

        return [
            {(k if k != "_id" else "id"): v for k, v in item.items()}
            for item in results
        ]

    def put_n_post(
        self, collection_name: str, data: dict, method: str = "POST"
    ) -> Union[int, str]:
        item_id = self.get_id(collection_name, data)
        collection = self.db[collection_name]
        if method == "POST":
            upserted_item = collection.update_one(
                {"_id": item_id}, {"$set": data}, upsert=True
            )
        else:
            upserted_item = collection.replace_one({"_id": item_id}, data, upsert=True)
        return upserted_item.upserted_id or item_id

    def bulk_put_n_post(
        self, collection_name: str, items: List[dict], method: str = "POST"
    ) -> List[Union[int, str]]:
        self.bulk_get_ids(collection_name, items)
        collection = self.db[collection_name]
        if method == "POST":
            requests = [
                UpdateOne({"_id": item["id"]}, {"$set": item}, upsert=True)
                for item in items
            ]
        else:
            requests = [
                ReplaceOne({"_id": item["id"]}, item, upsert=True) for item in items
            ]
        collection.bulk_write(requests)
        return [item["id"] for item in items]

    def delete(self, collection_name: str, item_id: Union[int, str] = None) -> bool:
        collection = self.db[collection_name]
        if item_id:
            existed = collection.delete_one({"_id": item_id})
            return existed
        else:
            existed = collection.drop()
            return existed

    def all(self) -> dict:
        return {
            collection_name: [
                {(k if k != "_id" else "id"): v for k, v in item.items()}
                for item in self.db[collection_name].find()
            ]
            for collection_name in self.db.list_collection_names()
        }

    def reset(self) -> None:
        self.db.client.drop_database(self.db)

    def get_ids(self, collection_name: str) -> set:
        return {item["_id"] for item in self.db[collection_name].find()}
