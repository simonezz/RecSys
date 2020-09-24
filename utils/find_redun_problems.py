import time
import matplotlib.pyplot as plt
from PIL import Image
import os

'''

Using Cosine similarity in Elastic Search,
find similar images with input ID and plot images.

'''

inputDir = '/home/master/source/project/Recommender_SH/originalImages'

def handle_query(query, fvecs, result_df, es, INDEX_NAME): #input query = 문제 id

    SEARCH_SIZE = 4
    query_vector = fvecs[result_df.loc[int(query),'index']]

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'fvec') + 1.0",
                "params": {"query_vector": query_vector}
            }
        }
    }

    search_start = time.time()
    response = es.search(
        index=INDEX_NAME,
        body={
            "size": SEARCH_SIZE,  # 유사한 벡터 몇 개 찾을건지
            "query": script_query,
            "_source": {"includes": ["Id", "fvec"]}  # 일치하는 아이디
        }
    )
    search_time = time.time() - search_start

    print()

    print("search time: {:.2f} ms".format(search_time * 1000))

    redun_names = []

    for hit in response["hits"]["hits"]:
        if hit['_score'] == 2:
            redun_names.append(hit["_source"]["Id"],)
    return redun_names
