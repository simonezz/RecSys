import time
import math
from sklearn.preprocessing import normalize
import numpy as np
from elasticsearch.helpers import bulk

# Bulk feature vectors to Elastic Search.
def data_bulk(es, result_df, INDEX_FILE, INDEX_NAME, fvec_file):

    dim = 1280
    bs = 10
    # Index 생성
    es.indices.delete(index=INDEX_NAME, ignore=[404])  # Delete if already exists

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        es.indices.create(index=INDEX_NAME, body=source)  # Create ES index

    fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)

    nloop = math.ceil(fvecs.shape[0] / bs)
    for k in range(nloop):

        rows = [{'_index': INDEX_NAME,
                 'Id': f'{list(result_df.index)[i]}', 'fvec': list(normalize(fvecs[i:i+1])[0].tolist())}
                for i in range(k * bs, min((k + 1) * bs, fvecs.shape[0]))]
        s = time.time()
        bulk(es, rows)
        print(k, time.time() - s)

    es.indices.refresh(index=INDEX_NAME)
    print(es.cat.indices(v=True))

