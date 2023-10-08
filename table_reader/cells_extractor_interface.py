from abc import ABC, abstractmethod


class CellsExtractorInterface(ABC):
    @abstractmethod
    def extract_cells(self, img: list) -> list:
        pass
