from collections import Counter
from enum import Enum

import matplotlib.pyplot as plt
import pytagcloud
from PyKomoran import *
from konlpy.tag import *


class TokenMode(Enum):
    hannanum = 1
    kkma = 2
    komoran = 3
    mecab = 4
    okt = 5


hannanum = Hannanum()  # 한나눔. KAIST Semantic Web Research Center 개발.
kkma = Kkma()  # 꼬꼬마. 서울대학교 IDS(Intelligent Data Systems) 연구실 개발.
komoran = Komoran()  # 코모란. Shineware에서 개발.
# mecab = Mecab()       # 메카브. 일본어용 형태소 분석기를 한국어를 사용할 수 있도록 수정.
# Install guide : https://i-am-eden.tistory.com/9
okt = Okt()  # Open Korean Text: 오픈 소스 한국어 분석기. 과거 트위터 형태소 분석기.


def tokeniz_morphs(string, mode=TokenMode.okt):
    if mode is TokenMode.hannanum:
        morphs = hannanum.morphs(string)
    elif mode is TokenMode.kkma:
        morphs = kkma.morphs(string)
    elif mode is TokenMode.komoran:
        morphs = komoran.morphs(string)
    elif mode is TokenMode.mecab:
        # morphs = mecab.morphs(string)
        print("Mecab는 추가설치가 필요합니다.")
    elif mode is TokenMode.okt:
        morphs = okt.morphs(string)
    return morphs


def tokeniz_nouns(string, mode=TokenMode.okt):
    if mode is TokenMode.hannanum:
        nouns = hannanum.nouns(string)
    elif mode is TokenMode.kkma:
        nouns = kkma.nouns(string)
    elif mode is TokenMode.komoran:
        nouns = komoran.nouns(string)
    elif mode is TokenMode.mecab:
        # nouns = mecab.nouns(string)
        print("Mecab는 추가설치가 필요합니다.")
    elif mode is TokenMode.okt:
        nouns = okt.nouns(string)
    return nouns


def tokeniz_pos(string, mode=TokenMode.okt):
    if mode is TokenMode.hannanum:
        pos = hannanum.pos(string)
    elif mode is TokenMode.kkma:
        pos = kkma.pos(string)
    elif mode is TokenMode.komoran:
        pos = komoran.pos(string)
    elif mode is TokenMode.mecab:
        # pos = mecab.pos(string)
        print("Mecab는 추가설치가 필요합니다.")
    elif mode is TokenMode.okt:
        pos = okt.pos(string)
    return pos


# 수학 용어 사용자 사전 등록 후 komoran 사용
# !pip install PyKomoran


# 사용자 사전이 등록된 komoran 모델 생성
def customize_komoran_model(tsv_file_path):
    komoran = Komoran(DEFAULT_MODEL['FULL'])
    komoran.set_user_dic(tsv_file_path)

    return komoran


# 코모란 모델을 통해 필요한 품사 단어만 뽑기
def komoran_usr_dic(komoran, text):
    word_classes = ['NNG', 'NNP', 'NNB', 'NR', 'VV', 'VA', 'MM', 'EF', 'MAG', 'MAJ']  # 사용할 품사 리스트

    return komoran.get_morphes_by_tags(text, tag_list=word_classes)


# word cloud 그리기 (pytagcloud 설치를 위해서는 pygame, simplejson이 설치되어 있어야 한다.)
# !pip install pygame
# !pip install simplejson
# !pip install pytagcloud
# site-packages/pytagcloud/fonts 에 한글 폰트 ttf 추가해주고 fonts.json에 추가해줘야함.(참고: https://ericnjennifer.github.io/python_visualization/2018/01/21/PythonVisualization_Chapt3.html)

def draw_word_cloud(text, save_path):
    taglist = pytagcloud.make_tags(Counter(text).most_common(200), maxsize=100)
    print(taglist)

    pytagcloud.create_tag_image(taglist, save_path, size=(900, 600), fontname='NanumMyeongjo')
    img = plt.imread(save_path)

    plt.imshow(img)
    plt.show()

    return
