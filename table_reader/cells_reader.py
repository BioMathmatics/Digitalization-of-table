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

        def read(self, img):
            s = None
            if self.name == 'easyocr':
                s = ' '.join(self.model.readtext(img, detail=0))
            elif self.name == 'tesseract':
                pass
            elif self.name == 'trocr-base-stage1':
                pass
            return s

    def __get_models(self, models: str, lang: list):
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

    def read_cells(self, columns_list: list, img: list) -> list:
        reg = '[€@\|\&<>#\$\'\":\^\*\\/=_\!№;\?\~©\[\]\{\}°™“`«»]'
        pattern = re.compile(reg)
        p_ban_char = lambda s: pattern.search(s) is not None

        table = [[] for i in range(len(columns_list))]
        for index, col in enumerate(columns_list):
            for cell in col:
                x, y, w, h = cell
                im = img[y: y + h, x:x + w]

                out = []
                for model in self.models:
                    out.append(model.read(im))

                s1 = out[0]
                s2 = out[-1]

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
