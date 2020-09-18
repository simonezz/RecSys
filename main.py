from elasticsearch import Elasticsearch
import numpy as np

from find_similar_problems import *
from prepare_data import *
from bulk_feature_vectors import *
import time

if __name__ == "__main__":

    prob_db = pymysql.connect(
        user='real',
        passwd='vmfl515!dnlf',
        host='sorinegi-cluster.cluster-ro-ce1us4oyptfa.ap-northeast-2.rds.amazonaws.com',
        db='iclass',
        charset='utf8'
    )
    dim = 1280
    es = Elasticsearch(hosts=['localhost:9200'])

    ID = input("Enter ID: ")  # Enter an ID that you want to find similar problems with.
    unit_code, problem_level = get_info(ID, prob_db)  # Get information of query ID.
    df = get_cand(unit_code, problem_level, prob_db)  # Dataframe of same unitCode, problemLevel problems.

    batch_size = 100
    input_shape = (224, 224, 3)
    input_dir = '/home/master/source/project/Recommender_SH/originalImages'  # directory which has image files.
    fvec_file = 'fvecs.bin'  # a file to save feature vectors.

    tmp = "/home/master/source/project/Recommender_SH/test_sh"+str(fvec_file)
    if os.path.isfile(tmp):
        os.remove(tmp)  # 이미 있으면 제거

    extract_feature(df, batch_size, input_shape, input_dir, fvec_file)  # save feature vectors to fvec_file.

    INDEX_NAME = 'test'
    INDEX_FILE = 'index.json'

    # bs = 10
    data_bulk(es, df, INDEX_FILE, INDEX_NAME, fvec_file)

    fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)



    handle_query(ID, fvecs, df, es, INDEX_NAME)
