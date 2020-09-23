

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
import tqdm
import requests, io
from PIL import Image

# data 불러옴
def get_all_info(prob_db):

    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = "SELECT ID, unitCode, problemLevel, problemURL FROM iclass.Table_middle_problems where isHide=0"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())


    return df


def preprocess_url(res, input_shape):

    img = tf.image.decode_jpeg(res.content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img

# batch별로 데이터 elasticsearch에 넣음
def bulk_batchwise(es, part_df, INDEX_NAME, INDEX_FILE):

    part_df.set_index("ID", inplace=True)

    input_shape = (224, 224, 3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))


    id_list = []
    res_list = []
    for i in list(part_df.index):
        url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i,'problemURL'] + "p.png"
        url = url.replace("/math_problems/", "/math_problems/d/")
        try:
            res = requests.get(url)
            id_list.append(i)
            res_list.append(res)
        except:
            print("ID : ", i, "의 url이 유효하지 않습니다.")
            pass

    list_ds = tf.data.Dataset.from_tensor_slices(res_list)
    ds = list_ds.map(lambda x: preprocess_url(x, input_shape), num_parallel_calls=-1)

    dataset = ds.batch(batch_size).prefetch(-1)

    for batch in dataset:
        fvecs = model.predict(batch)

    bulk(es, [{'_index': INDEX_NAME,
                 'Id': f'{id_list[i]}', 'fvec': list(normalize(fvecs[i:i+1])[0].tolist()), 'unitCode' : f'{part_df.loc[id_list[i],'unitCode'}', 'problemLevel' : f'{part_df.loc[id_list[i],'problemLevel'}'}
                for i in range(len(id_list))])

    return


# 모든 데이터를 넣음
def bulk_all(df, INDEX_FILE, INDEX_NAME):

    es = Elasticsearch(hosts=['localhost:9200'])
    dim = 1280
    bs = 10
    # Index 생성
    es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        es.indices.create(index=INDEX_NAME, body=source)  # Create ES index
    print("Elasticsearch Index :", INDEX_NAME, "created!")
    nloop = math.ceil(df.shape[0] / bs)

    for k in tqdm(range(nloop)):

        bulk_batchwise(es, df.loc[k*bs:min((k+1)*bs, df.shape[0])],INDEX_NAME, INDEX_FILE)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))

if __name__=="__main__":

    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )
    df = get_all_info(prob_db)

    INDEX_FILE = '../Test2/system/index2.json'
    INDEX_NAME = 'all_images'

    bulk_all(df, INDEX_FILE, INDEX_NAME)

    print("Success!")