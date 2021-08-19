# -*- coding: utf-8 -*-

import fitz
import os
import re
from collections import namedtuple
import logging

# Logger
dir_path = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(level=logging.DEBUG,
                    filename=r'{}'.format(os.path.join(dir_path, 'debug.log')),
                    filemode='w',
                    format='%(asctime)s %(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


def get_text_from_annots(file_name):
    output_text = ""
    Word = namedtuple('Word', ['x0', 'y0', 'x1', 'y1', 'word'])
    
    with fitz.open(file_name) as doc:
        for page in doc:
            words = page.getText("words")
            for annot in page.annots():
                annot_name = annot.info.get("content")
                rect = annot.rect

                if annot_name:
                    output_text += f'{annot_name}:\n====================\n'
                    ahu_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in rect]
                    output_text += pars_sort(ahu_pars)

    return output_text

def pars_sort(ahu_pars, output=""):
    try:
        ahu_pars.sort(key=lambda x: x.y1)

        # grouping by y1 value
        grouped_ahu_pars = [[ahu_pars[0]]]
        y1_tolerance = 1.0

        for item in ahu_pars[1:]:
            if item.y1 - grouped_ahu_pars[-1][0].y1 < y1_tolerance:
                grouped_ahu_pars[-1].append(item)
            else:
                grouped_ahu_pars.append([item])

        for group in grouped_ahu_pars:
            sort_group = sorted(group, key=lambda x: x.x0)
            row = ''
            x_tolerance = 3.5
            for idx, tup in enumerate(sort_group):
                if idx < (len(sort_group) - 1):
                    if sort_group[idx+1].x0 - sort_group[idx].x1 < x_tolerance:
                        row += f'{tup.word} '
                    else:
                        row += f'{tup.word}, '
                else:
                    row += f'{tup.word}, '
            output += f'{row}\n====================\n'

    except Exception as e:
        logger.info(ahu_pars)
        logger.error(e, exc_info=True)
        pass

    return output


def add_annots(file_name, source_doc):
    current_doc = fitz.open(file_name)
    current_doc_pages = dict(map(lambda x: (x.number, x), current_doc.pages()))

    try:
        for page in source_doc:
            page_num = page.number
            current_doc_page = current_doc_pages.get(page_num)  # get the corresponding page

            for annot in page.annots():
                annot_rect = annot.rect
                annot_border = annot.border
                annot_colors = annot.colors
                annot_info = annot.info
                popup_rect = annot.popup_rect

                new_annot = current_doc_page.add_rect_annot(annot_rect)  # create new rect annotation
                new_annot.set_border(**annot_border)  # set border from existing annotation
                new_annot.set_colors(**annot_colors)  # set color from existing annotation
                new_annot.set_popup(popup_rect)  # set popup from existing annotation
                new_annot.set_info(annot_info)  # set info from existing annotation
                new_annot.update(opacity=0.5)  # update new annotation

        if current_doc.can_save_incrementally():
            current_doc.save(file_name, incremental=True, encryption=0)

    except Exception as e:
        import traceback
        traceback.format_exc(e)

    finally:
        current_doc.close()


def find_text(doc):

    ahu_sections = [
        ('AHU_NAME',   r'(?:Номер|Название|№|Имя)\sустановки\s*(\w+)'),
        ('SILENCER',   r'(?:блок\s)?шумоглушител[ья]|silencer|sound attenuator'),
        ('FILTER',   r'(?:карманный\s)?фильтр(?![аовму]+)|filter'),
        ('HEAT_RECOVERY_SUPPLY',   r'(?:нагреватель\s)?гликол\.?(?:иевый)? рекуператор(?![аовму]+)|(?:glycol\s)?energy recovery'),
        ('HEAT_RECOVERY_EXHAUST',   r'(?:охладитель\s)?гликол\.?(?:иевый)? рекуператор(?![аовму]+)|(?:glycol\s)?energy recovery'),
        ('HEATER',   r'(?:водяной\s)?(?:на|подо|обо)греватель(?:\sвоздуха)?|(?:air\s)?heater'),
        ('COOLER',   r'(?:водяной|фреоновый)?\s?охладитель(?:\sвоздуха)?|(?:Water|DX)\s?(air\s)?cooler'),
        ('FAN',   r'вентилятор(?![аовму]+)|fan'),
        ]
    ahu_regex = '|'.join('(?P<%s>%s)+?' % pair for pair in ahu_sections)

    hex_pars_air = [
        ('AIR_FLOW_RATE',   r'(?:расход(?!\sсреды)(?:\sвоздуха)?)\s*\[?\w*\/?\w*\]?\,\s(\d{1,4}[\,\.]?\d{1,4})'),
        ('AIR_VELOCITY',   r'(?:скорость(?!\sсреды|\sтеплоносителя)(?:\sвоздуха)?)\s*\[?\w*\/?\w*\]?\,\s(\d{1,4}\,?\d{1,4})'),
        ('INLET_TEMP',   r'(?:температура\s)?воздуха?\sна\sвходе\s*\[?\w*\]?\,\s(\-?\d{1,3}\,?\d{0,2})'),
        ('OUTLET_TEMP',   r'(?:температура\s)?воздуха?\sна\sвыходе\s*\[?\w*\]?\,\s(\-?\d{1,3}\,?\d{0,2})'),
        ('AIR_PR_DROP',   r'(?:пот\.?(?:ер[ия])?\s?давл\.?(?:ения\s)?\s?по\sвоздуху)\s*\[?\w*\]?\,\s(\-?\d{1,3}\,?\d{0,2})'),
        ('CAPACITY',   r'(?:пр[оизводительно-]+сть|мощность)\s*\[?\w*\]?\,\s(\-?\d{1,3}\,?\d{0,2})')
    ]

    hex_pars_water = [
        ('MEDIUM',   r'(?:теплоноситель|среда)\s*\,\s(\d{0,2}\s?\%\s?\w+\s?\w+)'),
        ('MEDIUM_FLOW_RATE',   r'(?:расход(?!\sвоздуха)(?:\sсреды)?)\s*\[?\w*\/?\w*\]?\,\s(\d{1,4}\,.?\d{1,4})'),
        ('MEDIUM_VELOCITY',   r'(?:скорость(?!\sвоздуха)(?:\sтеплоносителя)?)\s*\[?\w*\/?\w*\]?\,\s(\d{1,4}\,?\d{1,4})'),
        ('MEDIUM_IN_OUTLET_TEMP',   r"""(?:температура\s)?(?:теплоносител[ья]|сред[ыа]\s)?(?:на\s)?входе?\s\/\s(?:температура\s)?
                                            (?:теплоносител[ья]|сред[ыа]\s)?(?:на\s)?выходе?\s*\[?\w*\]?\,\s(\-?\d{1,3}\,?
                                            \d{0,2})\s\/\s(\-?\d{1,3}\,?\d{0,2})"""),
        ('MEDIUM_INLET_TEMP',   r'(?:температура\s)?(?:теплоносител[ья]|сред[ыа]\s)(?:на\s)?входе?'),
        ('MEDIUM_OUTLET_TEMP',   r'(?:температура\s)?(?:теплоносител[ья]|сред[ыа]\s)(?:на\s)?выходе?'),
        ('MEDIUM_PR_DROP',   r'(?:пот\.?(?:ер[ия])?\s?давл\.?(?:ения\s)?\s?(?:теплоносител[ья]|сред[ыа]))\s*\[?\w*\]?\,\s(\d{1,3}\,?\d{0,2})'),
        ('MEDIUM_HEX_VOLUME',   r'(?:объем(?:\sтеплоносител[ья]|сред[ыа])?)\s*\[?\w*\]?\,\s(\d{1,3}\,?\d{0,2})'),
        ('HEX_ROWS',   r'рядность\s*\,\s(\d)'),
        ('HEX_INLET_DN',   r'(?:соединение|диаметр подсоединения)\s(?:на\s)?вход[еа]?\s*\,\s([dnду]{0,2}\s?\d{1,2}\/?\d{1,2}?)'),
        ('HEX_OUTLET_DN',   r'(?:соединение|диаметр подсоединения)\s(?:на\s)?выход[еа]?\s*\,\s([dnду]{0,2}\s?\d{1,2}\/?\d{1,2}?)')
    ]
    hex_pars_air_regex = '|'.join('(?P<%s>%s)+?' % pair for pair in hex_pars_air)
    hex_pars_water_regex = '|'.join('(?P<%s>%s)+?' % pair for pair in hex_pars_water)

    Word = namedtuple('Word', ['x0', 'y0', 'x1', 'y1', 'word', 'page_number'], defaults=(None,) * 6)
    PageRect = namedtuple('Page', ['x0', 'y0', 'x1', 'y1'], defaults=(None,) * 4)


    doc_pages = dict(map(lambda x: (x.number, x), doc.pages()))
    ahu_data = {}
    key_words = []
    page_rect = PageRect(*(doc_pages[0].rect))

    for page in doc:

        words = page.getText("words")
        prev_match = ""

        for w in words:
            match = re.fullmatch(ahu_regex, w[4], flags=re.IGNORECASE)
            if match:
                print(match.lastgroup)
                if match.group(0) != prev_match:
                    word = Word(*w[:5], page_number=page.number)
                    key_words.append(word)
                    prev_match = match.group(0)
    print(key_words)
    for idx, cur_word in enumerate(key_words):
        if idx < (len(key_words) - 1):
            page = doc_pages.get(cur_word.page_number)
            words = page.getText("words")
            next_word = key_words[idx + 1]

            if cur_word.page_number == next_word.page_number:
                sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, next_word.y0)
                section_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in sec_rect]
                if len(section_pars) > 0:
                    sorted_text = pars_sort(section_pars)
                    # print(sorted_text)

                    for rexp in (hex_pars_air_regex, hex_pars_water_regex):
                        for match in re.finditer(rexp, sorted_text, flags=re.IGNORECASE|re.VERBOSE):
                            if match:
                                value = list(filter(lambda x: x, match.groups()))
                                print(f"{match.lastgroup} - {value[1]}")


                    # words_list = sorted_text.split(", ")
                    # print(words_list)
                    # for idx, item in enumerate(words_list):
                    #     if idx < (len(words_list) - 1):
                    #         match = re.search(heat_exchanger_regex, item, flags=re.IGNORECASE)
                    #         if match:
                    #             print(f"{match.lastgroup}-{words_list[idx+1]}")
                

            else:
                two_pages_text = ""
                next_page = doc_pages.get(next_word.page_number)
                next_page_words = next_page.getText("words")
                cur_page_sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, page_rect.y1)
                next_page_sec_rect = fitz.Rect(page_rect.x0, page_rect.y0, page_rect.x1, next_word.y0)
                cur_page_sec_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in cur_page_sec_rect]
                next_page_sec_pars = [Word(*w[:5]) for w in next_page_words if fitz.Rect(w[:4]) in next_page_sec_rect]

                for item in (cur_page_sec_pars, next_page_sec_pars):
                    if len(item) > 0:
                        sorted_text = pars_sort(item)
                        two_pages_text += sorted_text
                # print(two_pages_text)

                for rexp in (hex_pars_air_regex, hex_pars_water_regex):
                        for match in re.finditer(rexp, two_pages_text, flags=re.IGNORECASE|re.VERBOSE):
                            if match:
                                value = list(filter(lambda x: x, match.groups()))
                                print(f"{match.lastgroup} - {value[1]}")


def main():
    dir_name = os.path.dirname(__file__)
    source_file_name = os.path.join(dir_name + "\\Test_Folder\\16638.2 ТЕХНИКА (РЕЖИМ производство).pdf")
    folder_path = os.path.join(dir_name + "\\Test_Folder\\test2\\")
    output_text = ''

    with fitz.open(source_file_name) as source_doc:
        find_text(source_doc)
    #     with os.scandir(folder_path) as files:
    #         for file in files:
    #             if file.is_file() and file.name.endswith('.pdf'):
    #                 pdf_file_name = os.path.join(folder_path + file.name)
    #                 add_annots(pdf_file_name, source_doc)

    #                 output_text += get_text_from_annots(pdf_file_name) + "\n***************************\n"

                    
    # with open('output.txt', 'w', encoding='utf-8') as fg:
    #     fg.write(output_text)


if __name__ == "__main__":
    main()
