#-*-coding:utf-8-*-
import math
import sys
import time

sys.path.append('../')

import pandas as pd
import pymysql
import requests
import tensorflow as tf
import tensorflow.keras.layers as layers
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sklearn.preprocessing import normalize
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import Model
from tqdm import tqdm
from utils import hwpmath2latex
import re
from PyKomoran import *
# data 불러옴
def get_all_info(prob_db, unitCode=None, datetime=None):
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    if datetime:
        sql = f"SELECT ID, unitCode, problemLevel, problemURL, DateTime_Add, problemType FROM iclass.Table_middle_problems where DateTime_Add >= str_to_date({datetime},'%Y%m%d')"
    elif unitCode:
        sql = f'SELECT ID, unitCode, problemLevel, problemURL, problemType FROM iclass.Table_middle_problems WHERE curriculumNumber=15 and unitCode = {unitCode}'
    else:
        sql = "SELECT ID, unitCode, problemLevel, problemURL, problemType FROM iclass.Table_middle_problems WHERE curriculumNumber=15"

    curs.execute(sql)
    print("sql:", sql)
    df = pd.DataFrame(curs.fetchall())
    print(f"{df.shape[0]}개의 데이터가 처리될 예정입니다.")
    return df


def preprocess_from_url(content, input_shape):
    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img


# batch별로 데이터 elasticsearch에 넣음
def bulk_batchwise(es, part_df, INDEX_NAME, model, input_shape, komoran):

    batch_size=100
    word_classes = ['NNP', 'NNG', 'VV', 'JKB', 'MAG', 'MM', 'VA', 'XSV', 'EP', 'JX']
    part_df.set_index("ID", inplace=True)

    id_list = []
    img_list = []
    text_list = []

    for id in (list(part_df.index)):

        img_url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[id, 'problemURL'] + "p.png"
        img_url = img_url.replace("/math_problems/", "/math_problems/ng/")  # ng는 고화질, d는 저화질

        hwp_url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[id, 'problemURL'] + "p.hwp"
        hwp_url = hwp_url.replace("math_problems", "math_problems/hwp")

        try:
            # print(id, "::::", hwp_url)

            img_res = requests.get(img_url)  # png

            if hwpmath2latex.hwp_parser(hwp_url):
                txt = hwpmath2latex.hwp_parser(hwp_url)
            else: #Timeout
                pass
            # print(txt)
            img_url = None
            hwp_url = None

            txt = txt.strip()
            # print(txt)
            if txt[0]=="[":
                i=1
                while True:
                    if txt[i]=="]":
                        txt = txt[i+1:]
                        break
                    i+=1



            txt = " ".join(komoran.get_morphes_by_tags(re.sub('[^A-Za-z가-힣]', " ", txt), tag_list=word_classes))

            img_list.append(preprocess_from_url(img_res.content, input_shape))


            # print(txt2)

            text_list.append(txt)

            txt = None # excessive memory usage 방지
            id_list.append(id)


        except:  # png가 존재하지 않으면
            print(f'ID : {id} 의 url {img_url} or {hwp_url}이 유효하지 않습니다.')
            pass

    list_ds = tf.data.Dataset.from_tensor_slices(img_list)

    dataset = list_ds.batch(batch_size).prefetch(-1)

    for batch in dataset:
        fvecs = model.predict(batch)


    dataset = None # excessive memory usage 방지

    if len(id_list)<1:
        return
    bulk(es, [{'_index': INDEX_NAME,
               '_id': id_list[i], 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist()),
               'unitCode': part_df.loc[id_list[i], 'unitCode'], 'problemLevel': part_df.loc[id_list[i], 'problemLevel'],
               'problemType': part_df.loc[id_list[i], 'problemType'],
               'plainText': text_list[i]} for i in range(len(id_list))])
    fvecs = None

    return


# 모든 데이터를 넣음
def bulk_all(df, INDEX_FILE, INDEX_NAME, komoran):
    es = Elasticsearch(hosts=['localhost:9200'], timeout=100, max_retries=10, retry_on_timeout=True)
    bs = 10

    # Index 생성
    # es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists
    #
    # # mappings 정의
    # with open(INDEX_FILE) as index_file:
    #     source = index_file.read().strip()
    #     es.indices.create(index=INDEX_NAME, body=source)  # Create ES index
    # print("Elasticsearch Index :", INDEX_NAME, "created!")

    nloop = math.ceil(df.shape[0] / bs)

    input_shape = (224, 224, 3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False

    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    # komoran = customize_komoran_model('../utils/komoran_dict.tsv')

    # for k in tqdm(range(33521)):
    # reader = easyocr.Reader(['ko', 'en'], gpu=False)

    # for k in tqdm(range(698,nloop)):

    for k in tqdm(range(10,nloop)):
        bulk_batchwise(es, df.loc[k * bs:min((k + 1) * bs, df.shape[0])], INDEX_NAME, model, input_shape, komoran)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))


# def put_data(date_time):
if __name__ == "__main__":
    date_time = "20201218"
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )

    print(f'{date_time}이후로 추가된 문제를 가져옵니다.')
    df = get_all_info(prob_db, datetime = date_time)

    INDEX_FILE = '../test2/system/mapping_whole_img_text.json'
    INDEX_NAME = 'mathflat1'

    bulk_start = time.time()



    komoran = Komoran(DEFAULT_MODEL['FULL'])
    komoran.set_user_dic('../utils/komoran_dict2.tsv')

    # reader = easyocr.Reader(['ko', 'en'], gpu=False)

    bulk_all(df, INDEX_FILE, INDEX_NAME, komoran)

    print(f'총 데이터 {df.shape[0]}개 bulk 소요시간은 {time.time() - bulk_start}')
    print("Success!")


# if __name__ == "__main__":
#     prob_db = pymysql.connect(
#         user='real',
#         passwd='vmfl515!dnlf',
#         host='for-problem-query-cluster.cluster-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
#         db='iclass',
#         charset='utf8'
#     )
#     # unitCode = 331101009
#     # df = get_all_info(prob_db, unitCode)  # 전체 data 업로드
#     df = get_all_info(prob_db)
#
#     INDEX_FILE = '../test2/system/mapping_whole_img_text.json'
#     INDEX_NAME = 'mathflat1'
#     #
#     bulk_start = time.time()
#
#     from PyKomoran import *
#
#     komoran = Komoran(DEFAULT_MODEL['FULL'])
#     komoran.set_user_dic('../utils/komoran_dict2.tsv')
#
#     # reader = easyocr.Reader(['ko', 'en'], gpu=False)
#
#     bulk_all(df, INDEX_FILE, INDEX_NAME, komoran)

    # print("Hide data bulk 소요시간: ", time.time() - bulk_start)
    # print("201201 Success!")
