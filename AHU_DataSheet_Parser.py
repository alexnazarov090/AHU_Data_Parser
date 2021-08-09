# -*- coding: utf-8 -*-

import fitz
import os
from collections import namedtuple


def get_text(file_name):
    output = ""
    Word = namedtuple('Word', ['x0', 'y0', 'x1', 'y1', 'word'])
    
    with fitz.open(file_name) as doc:
        for page in doc:
            words = page.getText("words")
            for annot in page.annots():
                annot_name = annot.info.get("content")
                rect = annot.rect

                if annot_name:
                    output += f'{annot_name}:\n====================\n'
                    ahu_pars = [Word(*w[:5]) for w in words if fitz.Rect(w[:4]) in rect]
                    ahu_pars.sort(key=lambda x: x.y1)

                    # grouping by y1 value
                    grouped_ahu_pars = []
                    y1_tolerance = 1.0
                    for item in ahu_pars:
                        if len(grouped_ahu_pars) >= 1:
                            if item.y1 - grouped_ahu_pars[-1][0].y1 < y1_tolerance:
                                grouped_ahu_pars[-1].append(item)
                            else:
                                grouped_ahu_pars.append([item])
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

def main():
    dir_name = os.path.dirname(__file__)
    source_file_name = os.path.join(dir_name + "\\Test_Folder\\119-0239A_01000_PER.pdf")
    folder_path = os.path.join(dir_name + "\\Test_Folder\\test2\\")
    output_text = ''

    with fitz.open(source_file_name) as source_doc:

        with os.scandir(folder_path) as files:
            for file in files:
                if file.is_file() and file.name.endswith('.pdf'):
                    pdf_file_name = os.path.join(folder_path + file.name)
                    add_annots(pdf_file_name, source_doc)

                    output_text += get_text(pdf_file_name) + "\n***************************\n"
    
    with open('output.txt', 'w', encoding='utf-8') as fg:
        fg.write(output_text)

if __name__ == "__main__":
    main()
