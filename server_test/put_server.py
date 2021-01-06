import sys

sys.path.insert(0, '../utils')

# 특정 날짜를 포함한 이후로 새로 추가된 문제 데이터를 Elasticsearch에 넣기(색인화)

import pandas as pd
import pymysql
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import tensorflow.keras.layers as layers
from tensorflow.keras.models import Model
import time
import math
from sklearn.preprocessing import normalize
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch
from tqdm import tqdm
import requests


# data 불러옴
def get_all_info(prob_db, DateTime):
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = f"SELECT ID, unitCode, problemLevel, problemURL, DateTime_Add FROM iclass.Table_middle_problems where DateTime_Add >= str_to_date({DateTime},'%Y%m%d')"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())

    return df


def preprocess_from_url(content, input_shape):
    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img


# batch별로 데이터 elasticsearch에 넣음
def bulk_batchwise(es, part_df, INDEX_NAME, model, input_shape):
    # batch_size = 100

    part_df.set_index("ID", inplace=True)

    id_list = []
    img_list = []
    for i in list(part_df.index):

        url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i, 'problemURL'] + "p.png"
        url = url.replace("/math_problems/", "/math_problems/d/")
        try:
            res = requests.get(url)

            img_list.append(preprocess_from_url(res.content, input_shape))
            id_list.append(i)
        except:
            print(f'ID : {i} 의 url이 유효하지 않습니다.')
            pass
    #
    # list_ds = tf.data.Dataset.from_tensor_slices(img_list)
    # dataset = list_ds.batch(batch_size).prefetch(-1)
    #
    # for batch in dataset:
    #     fvecs = model.predict(batch)
    fvecs = model.predict(tf.convert_to_tensor(img_list))
    bulk(es, [{'_index': INDEX_NAME,
               '_id': id_list[i], 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist()),
               'unitCode': part_df.loc[id_list[i], 'unitCode'], 'problemLevel': part_df.loc[id_list[i], 'problemLevel']}
              for i in range(len(id_list))])

    return


# 모든 데이터를 넣음
def bulk_all(df, INDEX_FILE, INDEX_NAME):
    es = Elasticsearch(hosts=['localhost:9200'])
    dim = 1280
    bs = 10
    nloop = math.ceil(df.shape[0] / bs)

    input_shape = (224, 224, 3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False

    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    for k in tqdm(range(nloop)):
        bulk_batchwise(es, df.loc[k * bs:min((k + 1) * bs, df.shape[0])], INDEX_NAME, model, input_shape)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))

def put_data(date_time):
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )

    print(f'{date_time}이후로 추가된 문제를 가져옵니다.')
    df = get_all_info(prob_db, date_time)

    INDEX_FILE = '../test2/system/mapping_whole_img.json'
    INDEX_NAME = 'mathflat1'

    bulk_start = time.time()

    bulk_all(df, INDEX_FILE, INDEX_NAME)

    print(f'총 데이터 {df.shape[0]}개 bulk 소요시간은 {time.time() - bulk_start}')
    print("Success!")

#
# if __name__ == "__main__":
#     put_data("20201202")
