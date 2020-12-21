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


# data 불러옴
def get_all_info(prob_db, unitCode=None):
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    if unitCode:
        sql = f'SELECT ID, unitCode, problemLevel, problemURL, problemType FROM iclass.Table_middle_problems WHERE curriculumNumber=15 and unitCode = {unitCode}'
    else:
        sql = "SELECT ID, unitCode, problemLevel, problemURL, problemType FROM iclass.Table_middle_problems WHERE curriculumNumber=15"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())

    return df


def preprocess_from_url(content, input_shape):
    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img


# batch별로 데이터 elasticsearch에 넣음
def bulk_batchwise(es, part_df, INDEX_NAME, model, input_shape, komoran):
    batch_size = 100
    word_classes = ['NNP', 'NNG', 'VV', 'EC', 'JKB', 'MAG', 'MM', 'VA', 'XSV', 'EP', 'JX', 'SL']
    part_df.set_index("ID", inplace=True)

    id_list = []
    img_list = []
    text_list = []

    for i in tqdm(list(part_df.index)[13:]):
        img_url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i, 'problemURL'] + "p.png"
        img_url = img_url.replace("/math_problems/", "/math_problems/ng/")  # ng는 고화질, d는 저화질

        hwp_url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i, 'problemURL'] + "p.hwp"
        hwp_url = hwp_url.replace("math_problems", "math_problems/hwp")
        print(i, "::::", hwp_url)
        try:
            img_res = requests.get(img_url)  # png

            try:  # hwp 있을 때

                txt = hwpmath2latex.hwp_parser(hwp_url)
                print(txt)
                img_list.append(preprocess_from_url(img_res.content, input_shape))

                text_list.append(txt)

                id_list.append(i)

            except:  # hwp 없을 때 -> 사용하지 않음
                print("fail")
                pass

        except:  # png가 존재하지 않으면
            print(f'ID : {i} 의 url {img_url}이 유효하지 않습니다.')
            pass

    list_ds = tf.data.Dataset.from_tensor_slices(img_list)

    dataset = list_ds.batch(batch_size).prefetch(-1)

    for batch in dataset:
        fvecs = model.predict(batch)

    bulk(es, [{'_index': INDEX_NAME,
               '_id': id_list[i], 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist()),
               'unitCode': part_df.loc[id_list[i], 'unitCode'], 'problemLevel': part_df.loc[id_list[i], 'problemLevel'],
               'problemType': part_df.loc[id_list[i], 'problemType'],
               'plainText': text_list[i]} for i in range(len(id_list))])

    return


# 모든 데이터를 넣음
def bulk_all(df, INDEX_FILE, INDEX_NAME, komoran):
    es = Elasticsearch(hosts=['localhost:9200'])
    bs = 20
    # Index 생성
    es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists

    # mappings 정의
    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        es.indices.create(index=INDEX_NAME, body=source)  # Create ES index
    print("Elasticsearch Index :", INDEX_NAME, "created!")
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

    for k in tqdm(range(nloop)):
        bulk_batchwise(es, df.loc[k * bs:min((k + 1) * bs, df.shape[0])], INDEX_NAME, model, input_shape, komoran)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))

if __name__ == "__main__":
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )
    unitCode = 322001012
    df = get_all_info(prob_db, unitCode)  # 전체 data 업로드

    INDEX_FILE = '../test2/system/mapping_whole_img_text.json'
    INDEX_NAME = 'mathtest'
    #
    bulk_start = time.time()

    from PyKomoran import *

    komoran = Komoran(DEFAULT_MODEL['FULL'])
    komoran.set_user_dic('../utils/komoran_dict.tsv')

    # reader = easyocr.Reader(['ko', 'en'], gpu=False)

    bulk_all(df, INDEX_FILE, INDEX_NAME, komoran)

    # print("Hide data bulk 소요시간: ", time.time() - bulk_start)
    # print("201201 Success!")
