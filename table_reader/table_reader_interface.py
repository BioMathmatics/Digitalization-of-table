from abc import ABC, abstractmethod


class TableReaderInterface(ABC):

    @abstractmethod
    def read(self, img):
        pass