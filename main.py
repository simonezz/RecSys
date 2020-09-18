from elasticsearch import Elasticsearch
import numpy as np

from find_similar_problems import *
from prepare_data import *
from bulk_feature_vectors import *

if __name__ == "__main__":

    dim = 1280
    es = Elasticsearch(hosts=['localhost:9200'])

    ID = input("Enter ID: ") # Enter an ID that you want to find similar problems with.
    unit_code, problem_level = get_info(ID) # Get information of query ID.
    df = get_cand(unit_code, problem_level) # Dataframe of same unitCode, problemLevel problems.

    batch_size = 100
    input_shape = (224, 224, 3)
    input_dir = 'originalImages'  # directory which has image files.
    fvec_file = 'fvecs_4.bin'  # a file to save feature vectors.

    extract_feature(df, batch_size, input_shape) # save feature vectors to fvec_file.

    INDEX_NAME = 'test'
    INDEX_FILE = 'index.json'

    bs = 10

    data_bulk()

    fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)



    handle_query(ID)