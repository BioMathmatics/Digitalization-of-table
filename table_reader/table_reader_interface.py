from abc import ABC, abstractmethod


class Table_reader_interface(ABC):
    @abstractmethod
    def extract_cells(self, img: list) -> list:
        pass
