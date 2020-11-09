import argparse
import sys

import hwp_parser
import olefile
from PyKomoran import *

sys.path.append('../utils')

import re
from soynlp.hangle import compose, decompose, character_is_korean

doublespace_pattern = re.compile('\s+')


def jamo_sentence(sent):
    def transform(char):
        if char == ' ':
            return char
        cjj = decompose(char)
        if len(cjj) == 1:
            return cjj
        cjj_ = ''.join(c if c != ' ' else '-' for c in cjj)

        return cjj_

    sent_ = []
    for char in sent:
        if character_is_korean(char):
            sent_.append(transform(char))
        else:
            sent_.append(char)

    sent_ = doublespace_pattern.sub(' ', ''.join(sent_))
    return sent_


def jamo_to_word(jamo):
    jamo_list, idx = [], 0

    while idx < len(jamo):
        if not character_is_korean(jamo[idx]):
            jamo_list.append(jamo[idx])
            idx += 1

        else:
            jamo_list.append(jamo[idx:idx + 3])
            idx += 3
    word = ""

    for jamo_char in jamo_list:
        if len(jamo_char) == 1:
            word += jamo_char
        elif jamo_char[2] == "-":
            word += compose(jamo_char[0], jamo_char[1], " ")
        else:
            word += compose(jamo_char[0], jamo_char[1], jamo_char[2])
    return word


def tokeniz_hwp(tsv_path, hwpf):
    word_classes = ['NNG', 'NNP', 'NNB', 'NR', 'VV', 'VA', 'MM', 'EF', 'MAG', 'MAJ']  # 사용할 품사 리스트

    komoran = Komoran(DEFAULT_MODEL['FULL'])
    komoran.set_user_dic(tsv_path)

    hwpReader = hwp_parser.HwpReader(olefile.OleFileIO(hwpf))

    bodyText_dic = hwpReader.bodyStream()
    bodyText = " ".join(list(bodyText_dic.values()))

    return " ".join(komoran.get_morphes_by_tags(bodyText, tag_list=word_classes))


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='save_path', type=str)
    parser.add_argument('-hwp', dest='hwp_file', type=str)
    parser.add_argument('-tsv', dest='tsv_file', type=str)  # 몇번째 순위부터 가져올건지
    result = parser.parse_args()
    return result


if __name__ == "__main__":
    args = parse_arguments()
    with open(args.save_path, "a") as file:
        file.write("\n")
        file.write(jamo_sentence(tokeniz_hwp(args.tsv_path, args.hwp)))

    file.close()
