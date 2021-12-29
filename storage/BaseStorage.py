import uuid
from abc import ABC, abstractmethod
from typing import Union, List


class BaseStorage(ABC):
    def __init__(self):
        self.primary_type = None

    @abstractmethod
    def get_with_id(self, table_name: str, item_id: Union[int, str]) -> dict:
        pass

    @abstractmethod
    def get_without_id(self, table_name: str, where_params: list, meta_params: dict) -> list:
        pass

    @abstractmethod
    def put_n_post(self, table_name: str, data: dict, method: str = 'POST') -> Union[int, str]:
        pass

    def post(self, table_name: str, data: dict) -> Union[int, str]:
        return self.put_n_post(table_name, data, 'POST')

    def put(self, table_name: str, data: dict) -> Union[int, str]:
        return self.put_n_post(table_name, data, 'PUT')

    @abstractmethod
    def delete(self, table_name: str, item_id: Union[int, str] = None) -> bool:
        pass

    @abstractmethod
    def all(self):
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    def get_items(self, collection_name) -> List[dict]:
        return []

    def get_id(self, collection_name: str, data: dict):
        item_id = data.get('id')
        if not item_id:
            item_ids = {item['id'] for item in self.get_items(collection_name)}
            if self.primary_type == int:
                item_id = max(item_ids or {0}) + 1
            elif self.primary_type == str:
                while True:
                    item_id = str(uuid.uuid4())
                    if item_id not in item_ids:
                        break
            data['id'] = item_id
        return item_id
