# -*- coding: utf-8 -*-
import collections
from pprint import pprint

import PyPDF2

import general_utils as utils


def get_pdf_info(reader):
    info = reader.getDocumentInfo()
    num_pages = reader.getNumPages()
    print(info)
    return info, num_pages


def extract_texts_from_page(reader, page_num):
    page = reader.getPage(page_num)
    print('Page type: {}'.format(str(type(page))))
    text = page.extractText()
    return text


def extract_texts_from_all_pages(reader):
    texts = []
    for i in range(len(reader.pages)):
        text = extract_texts_from_page(reader, i)
        texts.append(text)
    return texts


def walk(obj, fonts, embs):
    if not hasattr(obj, 'keys'):
        return None, None

    if '/BaseFont' in obj:
        fonts.add(obj['/BaseFont'])

    for k in obj.keys():
        walk(obj[k], fonts, embs)

    return fonts, embs  # return the sets for each page


if __name__ == '__main__':
    pdf_path = "../inputSamples/"
    pdf_fnames = utils.get_filenames(pdf_path, extensions=utils.PDF_EXTENSIONS)
    pdf_fnames.sort(reverse=False)
    for file_idx, fname in enumerate(pdf_fnames):
        dir_name, core_name, ext = utils.split_fname(fname)
        reader = PyPDF2.PdfFileReader(fname)
        unique_fonts = set()
        unique_embs = set()
        font_dict = collections.defaultdict(int)

        try:
            for page_idx, page in enumerate(reader.pages):
                obj = page.getObject()

                # Extract unique font info.
                fonts, embs = walk(obj['/Resources'], set(), set())
                unique_fonts = unique_fonts.union(fonts)
                # unique_embs = unique_embs.union(embs)

                # Count font frequency
                for font in fonts:
                    font_dict[font] += 1

            sort_font_dict = collections.Counter(font_dict)
            print("[{}] 문제집명 : {}".format(file_idx + 1, core_name))
            if len(sort_font_dict) > 0:
                pprint(sort_font_dict.most_common(10))
                print()
            else:
                print("X\n")

        except PyPDF2.utils.PdfReadError:
            print("File has not been decrypted")
            pass
