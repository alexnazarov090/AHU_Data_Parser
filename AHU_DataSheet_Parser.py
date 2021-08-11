# -*- coding: utf-8 -*-

import fitz
import os
import re
from collections import namedtuple


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
        x_tolerance = 3.0
        for idx, tup in enumerate(sort_group):
            if idx < (len(sort_group) - 1):
                if sort_group[idx+1].x0 - sort_group[idx].x1 < x_tolerance:
                    row += f'{tup.word} '
                else:
                    row += f'{tup.word}, '
            else:
                row += f'{tup.word}, '
        output += f'{row}\n====================\n'
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


def find_text(file_name):

    ahu_sections = [
        ('SILENCER',   r'^шумоглушитель|^silencer|^sound attenuator'),
        ('BAG_FILTER',   r'^(карманный\s)?фильтр(?![аовму]+)|^bag filter'),
        ('PANEL_FILTER',   r'^(панельный\s)?фильтр(?![аовму]+)|^panel filter'),
        ('HEAT_RECOVERY_SUPPLY',   r'^(нагреватель\s)?гликол\.?(иевый)? рекуператор(?![аовму]+)|^(glycol\s)?heat recovery'),
        ('HEAT_RECOVERY_EXHAUST',   r'^(нагреватель\s)?гликол\.?(иевый)? рекуператор(?![аовму]+)|^(glycol\s)?heat recovery'),
        ('HEATER',   r'^нагреватель(\sвоздуха)?|^(air\s)?heater'),
        ('COOLER',   r'^охладитель(\sвоздуха)?|^(air\s)?cooler'),
        ('FAN',   r'^вентилятор(?![аовму]+)|^fan'),
        ]

    ahu_regex = '|'.join('(?P<%s>%s)' % pair for pair in ahu_sections)

    Word = namedtuple('Word', ['x0', 'y0', 'x1', 'y1', 'word', 'page_number'], defaults=(None,) * 6)
    PageRect = namedtuple('Page', ['x0', 'y0', 'x1', 'y1'], defaults=(None,) * 4)

    with fitz.open(file_name) as doc:

        doc_pages = dict(map(lambda x: (x.number, x), doc.pages()))
        key_words = []
        page_rect = PageRect(*(doc_pages[0].rect))

        for page in doc:
            words = page.getText("words")
            # ahu_pars = [Word(*w[:5]) for w in words]
            # sorted_text = pars_sort(ahu_pars)

            # for match in re.finditer(ahu_regex, sorted_text, flags=re.IGNORECASE):
            #     print(match)
            
            prev_match = ""
            for w in words:
                match = re.search(ahu_regex, w[4], flags=re.IGNORECASE)
                if match:
                    if match.group(0) != prev_match:
                        word = Word(*w[:5], page_number=page.number)
                        key_words.append(word)
                        prev_match = match.group(0)


        for idx, cur_word in enumerate(key_words):
            if idx < (len(key_words) - 1):
                page = doc_pages.get(cur_word.page_number)
                words = page.getText("words")
                next_word = key_words[idx + 1]
                if cur_word.page_number == next_word.page_number:
                    sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, next_word.y0)
                    section_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in sec_rect]
                    sorted_text = pars_sort(section_pars)
                    print(sorted_text)
                else:
                    two_pages_text = ""

                    next_page = doc_pages.get(next_word.page_number)
                    next_page_words = next_page.getText("words")
                    cur_page_sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, page_rect.y1)
                    next_page_sec_rect = fitz.Rect(page_rect.x0, page_rect.y0, page_rect.x1, next_word.y0)
                    cur_page_sec_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in cur_page_sec_rect]
                    next_page_sec_pars = [Word(*w[:5]) for w in next_page_words if fitz.Rect(w[:4]) in next_page_sec_rect]

                    for item in (cur_page_sec_pars, next_page_sec_pars):
                        sorted_text = pars_sort(item)
                        two_pages_text += sorted_text

                    print(two_pages_text)


def main():
    dir_name = os.path.dirname(__file__)
    source_file_name = os.path.join(dir_name + "\\Test_Folder\\119-0239A_01000_PER.pdf")
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
