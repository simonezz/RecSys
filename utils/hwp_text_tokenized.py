from collections import Counter
from urllib.request import Request, urlopen

import olefile
import pandas as pd
import pymysql
from PyKomoran import *
from hwp_parser import *
from tqdm import notebook

'''
문제 hwp로부터 text를 가져와 유형별 키워드를 뽑아내는 코드들

'''

word_classes = ['NNG', 'NNP', 'NNB', 'NR', 'VV', 'VA', 'MM', 'EF', 'MAG', 'MAJ']  # 필요한 품사 모음


# mysql로부터 문제 data 정보 가져옴
def data_load_from_sql():
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # dataframe형태로 사용

    sql = "SELECT ID, unitCode, problemLevel, problemURL FROM iclass.Table_middle_problems WHERE curriculumNumber=15 and hwpExist = 1"
    curs.execute(sql)
    result = curs.fetchall()
    result_df = pd.DataFrame(result)
    result_df.set_index("ID", inplace=True)

    return result_df


# s3 hwp url로부터 plain text를 뽑아냄.
def extract_text_from_url(df):
    for ind in notebook.tqdm(list(df.index)):

        url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + df.loc[ind, 'problemURL'] + "p.hwp"
        url = url.replace("math_problems", "math_problems/hwp")
        tmp = Request(url)
        try:
            tmp = urlopen(tmp).read()
            f = olefile.OleFileIO(tmp)

            hwpReader = HwpReader(f)
            bodyText_dic = hwpReader.bodyStream()

            bodyTextRefined = []
            for b in bodyText_dic.value():
                try:
                    if b[0] == '[':

                        i = 1
                        while True:

                            if b[i] == ']':
                                bodyTextRefined.append.(b[i + 1:])
                                break
                            i += 1
                    else:
                        bodyTextRefined.append(b)
                except:
                    pass
            df.loc[ind, 'text'] = ' '.join(bodyTextRefined)
        except:
            print(url)
            pass

        return df


# 문제 text를 토큰화
def tokenized_text(df):
    # konlpy중 하나인 komoran 사용
    komoran = Komoran(DEFAULT_MODEL['FULL'])

    # 사용자 사전 등록
    komoran.set_user_dic('./komoran_dict.tsv')

    df['komoran'] = 'NAN'

    for ind in notebook.tqdm(list(df.index)):

        try:
            df.at[ind, 'komoran'] = komoran.get_morphes_by_tags(df.loc[ind, 'refined'], tag_list=word_classes)

        except:
            print(df.loc[ind, 'refined'])
            pass

    return df


# Extract unitcode-wise most common keywords
def count_keywords(df, num=200):
    komo_df = df.groupby('unitCode').agg({'komoran': 'sum'})

    komo_df['count'] = 'NAN'

    for i in notebook.tqdm(list(komo_df.index)):
        komo_df.at[i, 'count'] = Counter(komo_df.loc[i, 'komoran'])

    return komo_df


if __name__ == "__main__":
    df1 = data_load_from_sql()  # 15년개정 데이터 불러오기

    df2 = extract_text_from_url(df1)  # problemURL로부터 text 가져오기

    df3 = tokenized_text(df2)  # 각 문제의 text를 토큰화

    df4 = count_keywords(df3)  # 토큰화한 텍스트에서 키워수 빈도수 카운트

    df4.head()
