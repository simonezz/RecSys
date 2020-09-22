

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


def preprocess(img_content, input_shape):
    #     img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img_content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)
    return img


def get_fvec(url):
    url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + url + "p.png"
    url = url.replace("/math_problems/", "/math_problems/d/")

    res = requests.get(url)

    input_shape = (224, 224, 3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))
    data = preprocess(res.content, input_shape)
    print(data.shape)

    return model.predict(data)


# batch별로 image->feature vectors -> elasticsearch
def bulk_batchwise(df, INDEX_FILE, INDEX_NAME):

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

        rows = []

        for i in range(k * bs, min((k + 1) * bs, df.shape[0])):

            try:
                fvecs = get_fvec(df.loc[i,'problemURL'])
                rows.append({'_index': INDEX_NAME, 'Id': df.loc[i,'ID'], 'fvec': list(normalize(fvecs)[0].tolist()), 'unitCode': df.loc[i,'unitCode'], 'problemLevel':df.loc[i,'problemLevel']})
            except:
                pass
        s = time.time()
        bulk(es, rows)
        print(k, time.time() - s)

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

    bulk_batchwise(df, INDEX_FILE, INDEX_NAME)

    print("Success!")