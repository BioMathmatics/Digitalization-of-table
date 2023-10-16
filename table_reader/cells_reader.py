from table_reader.cells_reader_interface import CellsReaderInterface
import easyocr
import re


class CellsReader(CellsReaderInterface):
    # proxy class
    class __Model:
        # This class is necessary because models have different methods name for read text from image
        # This class solving this problem
        def __init__(self, model: object, model_name: str, lang: str = 'rus'):
            self.lang = lang
            self.name = model_name
            self.model = model

        def simple_read(self, img):
            """
            This method design for run models with minimal numbers parameters
            """
            s = None
            if self.name == 'easyocr':
                s = ' '.join(self.model.readtext(img, detail=0))
            elif self.name == 'tesseract':
                pass
            elif self.name == 'trocr-base-stage1':
                pass
            return s

        def read_advance(self, img, allowlist=None, detail=0, min_size=10, height_ths=0.5, width_ths=0.5):
            """
            This method design for run models with a large number parameters
            """
            res = None
            if self.name == 'easyocr':
                res = self.model.readtext(img, detail=detail, allowlist=allowlist,
                                          min_size=min_size, height_ths=height_ths, width_ths=width_ths)
            return res

    def __get_models(self, models: str, lang: list):
        """
        This method return list of models, where all models have the same name methods for read text
        """
        models_name_list = models.split('+')
        models_list = []
        for name in models_name_list[0:2]:
            if name == 'easyocr':
                models_list.append(
                    self.__Model(model=easyocr.Reader(lang),
                                 model_name='easyocr')
                )
            elif name == 'tesseract':
                pass
            elif name == 'trocr-base-stage1':
                pass
            else:
                raise ValueError(f'Unknown model ({name}). \nAvailable models: easyocr, tesseract, trocr-base-stage1')
        return models_list

    def __init__(self, model: str = 'easyocr', lang: list = ['ru']):
        self.models = self.__get_models(models=model, lang=lang)

        self.allow_list_all = []
        self.allow_list_num = ['.', ',', '-']
        for i in range(ord('a'), ord('z') + 1):
            self.allow_list_all.append(chr(i))
        for i in range(ord('A'), ord('Z') + 1):
            self.allow_list_all.append(chr(i))
        for i in range(ord('а'), ord('я') + 1):
            self.allow_list_all.append(chr(i))
        for i in range(ord('А'), ord('Я') + 1):
            self.allow_list_all.append(chr(i))
        for i in range(0, 10):
            self.allow_list_num.append(str(i))
        self.allow_list_all += self.allow_list_num

    def read_cells(self, columns_list: list, img: list, method: str = 'simple') -> list:
        if method == 'simple':
            table = self.simple_read(columns_list, img)
        elif method == 'scan':
            table = self.scan_read(columns_list, img)
        else:
            raise ValueError(f'Not support method {method}')
        return table

    def simple_read(self, columns_list: list, img: list) -> list:
        """
        This method design for two model
        """
        #  character filter
        reg = '[€@\|\&<>#\$\'\":\^\*\\/=_\!№;\?\~©\[\]\{\}°™“`«»]'
        pattern = re.compile(reg)
        p_ban_char = lambda s: pattern.search(s) is not None

        #  run by all cells in the table
        table = [[] for i in range(len(columns_list))]
        for index, col in enumerate(columns_list):
            for cell in col:
                x, y, w, h = cell
                im = img[y: y + h, x:x + w]

                # read cell both models
                out = []
                for model in self.models:
                    out.append(model.simple_read(im))

                s1 = out[0]
                s2 = out[-1]

                # choose the best result
                if p_ban_char(s1):
                    cell_value = s2
                elif p_ban_char(s2):
                    cell_value = s1
                else:
                    num_dig_s1 = len(re.sub("[^0-9]", "", s1))
                    num_dig_s2 = len(re.sub("[^0-9]", "", s2))

                    cell_value = [s1, s2][num_dig_s1 < num_dig_s2]

                table[index].append(cell_value.replace('\n', ' '))

        return table

    def scan_read(self, columns_list: list, img: list) -> list:
        """
        This method design for one model -- easyocr
        """
        if len(self.models) > 1 or self.models[0].name != 'easyocr':
            raise ValueError(f'Scan method support only easyocr model')
        model = self.models[0]
        # run model on two admissible set character
        scan1 = model.read_advance(img, allowlist=self.allow_list_all, detail=1, min_size=0)
        scan2 = model.read_advance(img, allowlist=self.allow_list_num, detail=1, min_size=0)

        # Choose the must confident prediction
        result = []
        for pair in zip(scan1, scan2):
            val1, val2 = pair
            if val1[2] > val2[2]:
                result.append(val1)
            else:
                result.append(val2)

        # helper method
        def in_cell_check(val, cell, shift=5):
            a, b, c, d = val[0]
            x, y, w, h = cell
            return x - shift <= a[0] <= x + w + shift and y - shift - 5 <= a[1] <= y + h + shift

        # making an image of the table of read cells
        image_table = [[] for _ in range(len(columns_list))]

        # run by columns in columns list
        for idx_col, col in enumerate(columns_list):
            # run by elements in current column
            for idx_cell, cell in enumerate(col):
                #  find all read strings in current cell
                in_cell_list = [val[1] for idx, val in enumerate(result) if in_cell_check(val, cell) and val[2] >= 0.95]
                # if in current cell not found string
                if len(in_cell_list) == 0:
                    image_table[idx_col].append(None)
                else:
                    s = ' '.join(in_cell_list)
                    image_table[idx_col].append(s)

        #  making result table
        table = [[] for i in range(len(columns_list))]
        for idx_col, col in enumerate(columns_list):
            for idx_cell, cell in enumerate(col):
                #  if in an image table in current cell no element, then read it separately
                if (val := image_table[idx_col][idx_cell]) is None:
                    x, y, w, h = cell
                    im = img[y: y + h, x:x + w]
                    s = ' '.join(model.read_advance(im, detail=0, allowlist=self.allow_list_num, min_size=0))
                    table[idx_col].append(s)
                else:
                    table[idx_col].append(val)
        return table
        


