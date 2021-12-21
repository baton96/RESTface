from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    def get_with_id(self, table_name: str, item_id: int):
        pass

    @abstractmethod
    def get_without_id(self, table_name: str, where_params: list, meta_params: dict):
        pass

    @abstractmethod
    def post(self, table_name: str, data: dict):
        pass

    @abstractmethod
    def delete(self, table_name: str, item_id: int = None) -> bool:
        pass

    @abstractmethod
    def all(self):
        pass

    @abstractmethod
    def reset(self):
        pass

