

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
import numpy as np
import struct
import requests, io
from PIL import Image

# data 불러옴
def get_all_info(prob_db):

    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = "SELECT ID, unitCode, problemLevel, problemURL FROM iclass.Table_middle_problems where isHide=0"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())


    return df

def preprocess(img_path, input_shape):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=input_shape[2])
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)
    return img

# url -> Image -> feature vector
def get_fvec(url, input_dir):

    res = requests.get(url)
    img = Image.open(io.BytesIO(res.content)).convert('RGB')  # png image to jpg

    input_shape = (224,224,3)
    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    # fnames = [input_dir + '/test' + str(Id) + '.png' for Id in list(df.index)]
    # list_ds = tf.data.Dataset.from_tensor_slices(fnames)
    # ds = list_ds.map(lambda x: preprocess(x, input_shape), num_parallel_calls=-1)
    data = preprocess(img, input_shape)
    # dataset = ds.batch(batch_size).prefetch(-1)
    #
    # for batch in dataset:
    #     fvecs = model.predict(batch)
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

        for i in range(k * bs, min((k + 1) * bs, fvecs.shape[0])):

            try:
                fvecs = get_fvec(df.loc[i,'problemURL'])
                rows.append({'_index': INDEX_NAME, 'Id': f'{df.loc[i,'ID']}', 'fvec': list(normalize(fvecs)[0].tolist()), 'unitCode':f'{df.loc[i,'unitCode']}', 'problemLevel':f'{df.loc[i,'problemLevel']'})
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
    INDEX_NAME = 'AllImages'

    bulk_batchwise(df, INDEX_FILE=, INDEX_NAME=)

    print("Success!")