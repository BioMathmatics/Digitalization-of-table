import pandas as pd
from pdf2image import convert_from_bytes
import numpy as np

from table_reader.table_reader_interface import TableReaderInterface
from table_reader.cells_extractor_interface import CellsExtractorInterface
from table_reader.cells_extractor import CellsExtractor
from table_reader.cells_reader_interface import CellsReaderInterface
from table_reader.cells_reader import CellsReader
from table_reader.image_processing import align_image


def _list_to_pandas(table: list) -> pd.DataFrame:
    d = {}

    idx = 0
    for col in table:
        key = col[0].replace('\n', ' ')
        if key in d:
            key = key + f' {idx}'
            idx += 1
        d[key] = col[1::]

    table_pd = pd.DataFrame(data=d)
    return table_pd


class TableReader(TableReaderInterface):

    def __init__(self,
                 cell_extractor: CellsExtractorInterface = CellsExtractor(),
                 cell_reader: CellsReaderInterface = CellsReader(model='easyocr', lang=['ru', 'en'])):
        self.cell_extractor = cell_extractor
        self.cell_reader = cell_reader

    def read_pdf(self, pdf: bytes):
        pages = convert_from_bytes(pdf)
        df_list = []
        for page in pages:
            img = np.array(page)
            align_im = align_image(img)
            columns_list = self.cell_extractor.extract_cells(img)
            table = self.cell_reader.read_cells(columns_list, align_im, method='scan')
            df = _list_to_pandas(table)
            df_list.append(df)
        res_df = pd.DataFrame()
        for df in df_list:
            res_df = pd.concat([res_df, df], ignore_index=True)
        return res_df

    def read_image(self, img: list):
        align_im = align_image(img)
        columns_list = self.cell_extractor.extract_cells(img)
        table = self.cell_reader.read_cells(columns_list, align_im, method='scan')
        df = _list_to_pandas(table)
        return df

    def read(self, file: list or bytes, is_pdf=False):
        if is_pdf:
            df = self.read_pdf(file)
        else:
            df = self.read_image(file)
        return df
