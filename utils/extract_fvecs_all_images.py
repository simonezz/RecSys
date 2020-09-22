
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

'''

Input : problem ID

Result : Put feature vectors of all problems into ElasticSearch

'''
# Get input data information(unitCode, problemLevel) from MySQL
# You can find MySQL host, password info from Freewheelin notion -> Engineering wiki -> Credentials
def get_all_info(prob_db):

    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = "SELECT ID, unitCode, problemLevel, isHide FROM iclass.Table_middle_problems where isHide=0"

    curs.execute(sql)
    df = pd.DataFrame(curs.fetchall())
    df.set_index("ID", inplace=True)

    return df

tf.compat.v1.enable_eager_execution()

# Preprocess problem images to put them into MobileNet
def preprocess(img_path, input_shape):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=input_shape[2])
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)
    return img

# Put images into pre-trained MobileNet to extract feature vectors
def extract_feature(df, batch_size, input_shape, input_dir, fvec_file):

    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    fnames = [input_dir +'/test'+str(Id)+'.png' for Id in list(df.index)]
    list_ds = tf.data.Dataset.from_tensor_slices(fnames)
    ds = list_ds.map(lambda x: preprocess(x, input_shape), num_parallel_calls=-1)
    dataset = ds.batch(batch_size).prefetch(-1)
    #
    with open(fvec_file, 'wb') as f:
        for batch in dataset:
            fvecs = model.predict(batch)
            fmt = f'{np.prod(fvecs.shape)}f'
            f.write(struct.pack(fmt, *(fvecs.flatten())))
    return


# Bulk feature vectors to Elastic Search.
def all_data_bulk(es, result_df, INDEX_FILE, INDEX_NAME, fvec_file):

    dim = 1280
    bs = 10
    # Index 생성
    es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        es.indices.create(index=INDEX_NAME, body=source)  # Create ES index

    fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)

    nloop = math.ceil(fvecs.shape[0] / bs)
    for k in tqdm(range(nloop)):

        rows = [{'_index': INDEX_NAME,
                 'Id': f'{list(result_df.index)[i]}', 'fvec': list(normalize(fvecs[i:i+1])[0].tolist())}
                for i in range(k * bs, min((k + 1) * bs, fvecs.shape[0]))]
        s = time.time()
        bulk(es, rows)
        print(k, time.time() - s)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))

if __name__=="__main__":

    batch_size = 100
    input_shape = (224, 224, 3)
    input_dir = '/home/master/source/project/Recommender_SH/originalImages'

    fvec_file = 'fvecs.bin'
    INDEX_FILE = '../Test2/system/index2.json'
    INDEX_NAME = 'AllProblems'
    es = Elasticsearch(hosts=['localhost:9200'])
    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )
    df = get_all_info(prob_db)

    extract_feature(df, batch_size, input_shape, input_dir, fvec_file)

    all_data_bulk(es, df, INDEX_FILE, INDEX_NAME, fvec_file)


