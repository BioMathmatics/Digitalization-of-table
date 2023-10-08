from abc import ABC, abstractmethod


class CellsReaderInterface(ABC):
    @abstractmethod
    def read_cells(self, columns_list: list, img: list) -> list:
        pass
