from typing import Union, List

import pymongo

from .BaseStorage import BaseStorage


class MongoStorage(BaseStorage):
    def __init__(self, storage_path: str = None, uuid_id: bool = False):
        super().__init__()
        storage_path = storage_path or 'mongodb://localhost:27017'
        self.db = pymongo.MongoClient(storage_path).db
        self.primary_type = str if uuid_id else int

    def get_with_id(self, collection_name: str, item_id: Union[int, str]) -> dict:
        collection = self.db[collection_name]
        return {
            (k if k != '_id' else 'id'): v
            for k, v in (collection.find_one({'_id': item_id}) or {}).items()
        }

    def get_without_id(self, collection_name: str, where_params_raw: list, meta_params: dict) -> list:
        collection = self.db[collection_name]
        where_params = {}
        for op_name, param_name, param_value in where_params_raw:
            if param_name == 'id':
                param_name = '_id'

            if op_name == '=':
                if param_value == '':
                    where_params[param_name] = {'$exists': True}
                else:
                    where_params[param_name] = param_value
            else:
                where_params[param_name] = {('$' + op_name): param_value}

        desc = meta_params['desc']
        order_by = meta_params['order_by']
        order_key = [
            (order_by_arg if order_by_arg != 'id' else '_id', pymongo.DESCENDING if desc else pymongo.ASCENDING)
            for order_by_arg in order_by
        ]
        results = collection.find(
            filter=where_params,
            sort=order_key,
            skip=meta_params['_offset'],
            limit=meta_params['_limit']
        )

        return [
            {
                (k if k != '_id' else 'id'): v
                for k, v in item.items()
            } for item in results
        ]

    def put_n_post(self, collection_name: str, data: dict, method: str = 'POST') -> Union[int, str]:
        item_id = self.get_id(collection_name, data)
        collection = self.db[collection_name]
        if method == 'POST':
            data = {'$set': {k: v for k, v in data.items() if k != 'id'}}
            upserted_item = collection.update_one({'_id': item_id}, data, True)
        # elif method == 'PUT':
        else:
            data = {k: v for k, v in data.items() if k != 'id'}
            upserted_item = collection.replace_one({'_id': item_id}, data, True)
        return upserted_item.upserted_id or item_id

    def delete(self, collection_name: str, item_id: Union[int, str] = None) -> bool:
        collection = self.db[collection_name]
        if item_id:
            existed = collection.delete_one({'_id': item_id})
            return existed
        else:
            existed = collection.drop()
            return existed

    def all(self) -> dict:
        return {
            collection_name: [
                {
                    (k if k != '_id' else 'id'): v
                    for k, v in item.items()
                }
                for item in self.db[collection_name].find()
            ]
            for collection_name in self.db.list_collection_names()
        }

    def reset(self) -> None:
        self.db.client.drop_database(self.db)

    def get_items(self, collection_name) -> List[dict]:
        return [{'id': item['_id']} for item in self.db[collection_name].find()]
