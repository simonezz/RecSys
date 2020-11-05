import math
import time

import pandas as pd
import pymysql
import requests
import tensorflow as tf
import tensorflow.keras.layers as layers
from elasticsearch.helpers import bulk
from sklearn.preprocessing import normalize
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import Model

'''

Input : problem ID

Result : Put feature vectors of problems of same unitCode, problemLevel with Input ID into ElasticSearch

'''


# Get input data information(unitCode, problemLevel) from MySQL
# You can find MySQL host, password info from Freewheelin notion -> Engineering wiki -> Credentials
def get_similar_df(ID, prob_db):

    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = "SELECT unitCode, problemLevel, isHide FROM iclass.Table_middle_problems where ID = " + str(ID)

    curs.execute(sql)
    tmp = curs.fetchall()
    tmp_df = pd.DataFrame(tmp)


    unit_code = tmp_df.loc[0, 'unitCode']
    problem_level = tmp_df.loc[0, 'problemLevel']
    isHide = tmp_df.loc[0, 'isHide']

    if int(isHide) == 1:
        raise Exception("예외 발생: 숨겨진 문제입니다.")

# Get dataframe of problems with same unitCode, problemLevel with input ID.
    sql = "SELECT ID, unitCode, problemLevel, isHide, problemURL FROM iclass.Table_middle_problems where isHide = 0 and unitCode = "+ str(unit_code) + " and problemLevel = "+ str(problem_level)

    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # dataframe형태로 사용
    curs.execute(sql)
    result = curs.fetchall()
    result_df = pd.DataFrame(result)

    result_df = result_df.reset_index()
    result_df.set_index("ID", inplace=True)

    return result_df


tf.compat.v1.enable_eager_execution()

# Preprocess problem images to put them into MobileNet
def preprocess_from_url(content, input_shape):

    img = tf.io.decode_png(content, channels=3, name="jpeg_reader")
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)

    return img

# Put images into pre-trained MobileNet to extract feature vectors
def extract_feature_url(part_df, batch_size, input_shape):

    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    id_list = []
    img_list = []
    for i in list(part_df.index):
        url = "https://s3.ap-northeast-2.amazonaws.com/mathflat" + part_df.loc[i,'problemURL'] + "p.png"
        url = url.replace("/math_problems/", "/math_problems/d/")

        try:
            img_list.append(preprocess_from_url(requests.get(url).content, input_shape))
            id_list.append(i)

        except:
            print(f'ID : {i} 의 url({url}이 유효하지 않습니다.')
            pass

    list_ds = tf.data.Dataset.from_tensor_slices(img_list)
    # ds = list_ds.map(lambda x: preprocess_from_url(x, input_shape), num_parallel_calls=-1)

    dataset = list_ds.batch(batch_size).prefetch(-1)

    for batch in dataset:
        fvecs = model.predict(batch)

    return fvecs, id_list


# Bulk feature vectors to Elastic Search.
def data_bulk(es, result_df, INDEX_FILE, INDEX_NAME, fvecs):
    dim = 1280
    bs = 10
    # Index 생성
    # es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists
    #
    # with open(INDEX_FILE) as index_file:
    #     source = index_file.read().strip()
    #     es.indices.create(index=INDEX_NAME, body=source)  # Create ES index

    # fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)

    nloop = math.ceil(fvecs.shape[0] / bs)
    for k in range(nloop):
        rows = [{'_index': INDEX_NAME,
                 'Id': f'{list(result_df.index)[i]}', 'fvec': list(normalize(fvecs[i:i + 1])[0].tolist())}
                for i in range(k * bs, min((k + 1) * bs, fvecs.shape[0]))]
        s = time.time()
        bulk(es, rows)
        print(k, time.time() - s)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))



