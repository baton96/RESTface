from abc import ABC, abstractmethod
from typing import Union


class BaseStorage(ABC):
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
