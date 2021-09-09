# -*- coding: utf-8 -*-

import fitz
import os
import re
import logging
from collections import namedtuple
from regex_patterns import AHU_SEC_REGEX, HEX_PARS_AIR_REGEX, HEX_PARS_WATER_REGEX

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
        logger.error(e, exc_info=True)
        pass

    finally:
        current_doc.close()


def group_adjecent_words(ahu_pars, x_tolerance=0.0, y_tolerance=0.0, as_text=False):

    KeyPhrase = namedtuple('KeyPhrase', ['x0', 'y0', 'x1', 'y1', 'keyPhrase', 'page_number'], defaults=(None,) * 6)

    try:
        # sorting words by y1 coordinate
        ahu_pars.sort(key=lambda x: x.y1)
        # grouping by y1 coordinate
        grouped_ahu_pars = [[ahu_pars[0]]]
        for item in ahu_pars[1:]:
            # check if difference between y1 coordinates of the current and 
            # next words is less than y_tolerance
            if abs(item.y1 - grouped_ahu_pars[-1][0].y1) < y_tolerance:
                grouped_ahu_pars[-1].append(item)  # put them in the same group
            else:
                grouped_ahu_pars.append([item])  # put the next word in a different group(list)

        if as_text:
            key_phrases = ""
            for group in grouped_ahu_pars:
                sort_group = sorted(group, key=lambda x: x.x0)
                row = ''
                for idx, tup in enumerate(sort_group):
                    if idx < (len(sort_group) - 1):
                        if sort_group[idx+1].x0 - tup.x1 < x_tolerance:
                            row += f'{tup.word}_'
                        else:
                            row += f'{tup.word}-'
                    else:
                        row += f'{tup.word}-'
                key_phrases += f'{row}\n====================\n'

        else:
            key_phrases = []
            # group words by x coordinate
            for group in grouped_ahu_pars:
                sort_group = sorted(group, key=lambda x: x.x0)  # sort group by x0 coordinate
                prev = [sort_group[0]] # first word tuple
                for word in sort_group[1:]:
                    # check if difference between x0 coordinates of the current and 
                    # next words is less than x_tolerance
                    if word.x0 - prev[-1].x1 < x_tolerance:
                        prev.append(word)  # put them in the same word group

                        if word == sort_group[-1]:
                            # assemble key phrase/parameter name
                            key_phrase = KeyPhrase(prev[0].x0, 
                                                    prev[0].y0, 
                                                    prev[-1].x1, 
                                                    prev[-1].y1, 
                                                    "_".join(map(lambda x: x.word, prev)), 
                                                    prev[0].page_number)

                            key_phrases.append(key_phrase)

                    else:
                        # assemble key phrase/parameter name
                        key_phrase = KeyPhrase(prev[0].x0, 
                                                prev[0].y0, 
                                                prev[-1].x1, 
                                                prev[-1].y1, 
                                                "_".join(map(lambda x: x.word, prev)), 
                                                prev[0].page_number)

                        key_phrases.append(key_phrase)
                        prev = [word]

        return key_phrases

    except Exception as e:
        logger.error(e, exc_info=True)
        pass


def find_text(doc):

    Word = namedtuple('Word', ['x0', 'y0', 'x1', 'y1', 'word', 'page_number'], defaults=(None,) * 6)
    PageRect = namedtuple('Page', ['x0', 'y0', 'x1', 'y1'], defaults=(None,) * 4)


    doc_pages = dict(map(lambda x: (x.number, x), doc.pages()))
    ahu_data = {}
    section_name = ""
    sections = {}
    sections_added = {}
    ahu_keys = []
    page_rect = PageRect(*(doc_pages[0].rect))

    try:
        for page in doc:
            words = page.getText("words")
            ahu_pars = [Word(*w[:5], page_number=page.number) for w in words]
            grouped_ahu_pars = group_adjecent_words(ahu_pars, x_tolerance=10.0, y_tolerance=1.0)

            for idx, par in enumerate(grouped_ahu_pars):
                if idx < (len(grouped_ahu_pars) - 1):

                    if 'HEAT_RECOVERY_SUPPLY' in str(section_name) or 'HEATER' in str(section_name) or 'COOLER' in str(section_name):
                        for regexp in (HEX_PARS_AIR_REGEX, HEX_PARS_WATER_REGEX):
                            match = re.search(regexp, par.keyPhrase, flags=re.IGNORECASE)
                            if match:
                                value = re.search(r"^\-?\d{0,4}[\,\.]?\d{0,4}$", 
                                                par.keyPhrase, 
                                                flags=re.IGNORECASE)
                                if not value:
                                    value = re.search(r"^\-?\d{0,4}[\,\.]?\d{0,4}$", 
                                                        grouped_ahu_pars[idx+1].keyPhrase, 
                                                        flags=re.IGNORECASE)
                                if value:
                                    sections[section_name][1][match.lastgroup] = value.string

                    match = re.search(AHU_SEC_REGEX, par.keyPhrase, flags=re.IGNORECASE)

                    if match:
                        if str(match.lastgroup) == "AHU_NAME":
                            ahu_keys = list(ahu_data.keys())
                            ahu_name = re.search(r"AHU\s*.+|[ПВ]+\d+", 
                                                grouped_ahu_pars[idx].keyPhrase, 
                                                flags=re.IGNORECASE)
                            if not ahu_name:
                                ahu_name = re.search(r"AHU\s*.+|[ПВ]+\d+", 
                                                    grouped_ahu_pars[idx+1].keyPhrase, 
                                                    flags=re.IGNORECASE)

                            if ahu_name and ahu_name.string not in ahu_keys:
                                if len(ahu_keys) != 0:
                                    ahu_data[ahu_keys[-1]] = sections

                                ahu_data[ahu_name.string] = {}
                                sections = {}
                                sections_added = {}
                            continue

                        if match.lastgroup not in sections_added:
                            section_name = match.lastgroup
                            sections[section_name] = (par, {})

                        else:
                            if par.page_number == sections[match.lastgroup][0].page_number:
                                continue

                            if sections_added[match.lastgroup] > 2:
                                if par.page_number == sections[f"{match.lastgroup}_{sections_added[match.lastgroup]-1}"][0].page_number:
                                    continue

                            section_name = f"{match.lastgroup}_{sections_added[match.lastgroup]}"
                            sections[section_name] = (par, {})
                        sections_added[match.lastgroup] = sections_added.get(match.lastgroup, 1) + 1
                        continue

        ahu_data[ahu_keys[-1]] = sections
        print(ahu_data)
    except Exception as e:
        logger.error(e, exc_info=True)
        pass

    # try:
    #     for ahu, sections in ahu_data.items():
    #         sec_vals = list(sections.values())
    #         for idx, cur_word in enumerate(sec_vals):
    #             if idx < (len(sec_vals) - 1):
    #                 page = doc_pages.get(cur_word.page_number)
    #                 words = page.getText("words")
    #                 next_word = sec_vals[idx + 1]

    #                 if cur_word.page_number == next_word.page_number:
    #                     sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, next_word.y0)
    #                     section_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in sec_rect]
    #                     if len(section_pars) > 0:
    #                         sorted_text = group_adjecent_words(section_pars, x_tolerance=3.5, y_tolerance=1.0)

    #                         for rexp in (HEX_PARS_AIR_REGEX, HEX_PARS_WATER_REGEX):
    #                             for match in re.finditer(rexp, sorted_text, flags=re.IGNORECASE|re.VERBOSE):
    #                                 if match:
    #                                     value = list(filter(lambda x: x, match.groups()))
    #                                     print(f"{ahu}: {match.lastgroup} - {value}")

    #                 else:
    #                     two_pages_text = ""
    #                     next_page = doc_pages.get(next_word.page_number)
    #                     next_page_words = next_page.getText("words")
    #                     cur_page_sec_rect = fitz.Rect(page_rect.x0, cur_word.y0, page_rect.x1, page_rect.y1)
    #                     next_page_sec_rect = fitz.Rect(page_rect.x0, page_rect.y0, page_rect.x1, next_word.y0)
    #                     cur_page_sec_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in cur_page_sec_rect]
    #                     next_page_sec_pars = [Word(*w[:5]) for w in next_page_words if fitz.Rect(w[:4]) in next_page_sec_rect]

    #                     for item in (cur_page_sec_pars, next_page_sec_pars):
    #                         if len(item) > 0:
    #                             sorted_text = group_adjecent_words(section_pars, x_tolerance=3.5, y_tolerance=1.0)
    #                             two_pages_text += sorted_text

    #                     for rexp in (HEX_PARS_AIR_REGEX, HEX_PARS_WATER_REGEX):
    #                             for match in re.finditer(rexp, two_pages_text, flags=re.IGNORECASE|re.VERBOSE):
    #                                 if match:
    #                                     value = list(filter(lambda x: x, match.groups()))
    #                                     print(f"{ahu}: {match.lastgroup} - {value}")

    # except Exception as e:
    #     logger.error(e, exc_info=True)
    #     pass

def main():
    dir_name = os.path.dirname(__file__)
    source_file_name = os.path.join(dir_name + "\\Test_Folder\\119-0239A_01000_PER.pdf")
    folder_path = os.path.join(dir_name + "\\Test_Folder\\test2\\")
    output_text = ''

    with fitz.open(source_file_name) as source_doc:
        find_text(source_doc)
    
    # with fitz.open(source_file_name) as source_doc:
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
