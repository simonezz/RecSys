import time
import matplotlib.pyplot as plt
from PIL import Image
import os
import numpy as np
'''

Using Cosine similarity in Elastic Search,
find similar images with input ID and plot images.

'''

inputDir = '/home/master/source/project/Recommender_SH/originalImages'


def setAxes(ax, image, query=False, **kwargs):
    value = kwargs.get("value", None)
    if query:
        ax.set_xlabel("Query Image\n{0}".format(image), fontsize=12)
    else:
        ax.set_xlabel("Similarity value {1:1.3f}\n{0}".format(image, value), fontsize=12)
    ax.set_xticks([])
    ax.set_yticks([])


def plotSimilarImages(similarNames, similarValues, numCol):
    numRow = 1
    #     simImages, simValues = getSimilarImages(image, similarNames, similarValues)
    fig = plt.figure(figsize=(10, 20))

    # now plot the  most simliar images
    for j in range(0, numCol * numRow):
        ax = []
        if j == 0:
            img = Image.open(os.path.join(inputDir, similarNames[j]))
            ax = fig.add_subplot(numRow, numCol, 1)
            setAxes(ax, similarNames[j], query=True)
        else:
            img = Image.open(os.path.join(inputDir, similarNames[j]))
            ax.append(fig.add_subplot(numRow, numCol, j + 1))
            setAxes(ax[-1], similarNames[j], value=similarValues[j])
        img = img.convert('RGB')
        plt.imshow(img)
        img.close()

    plt.show()


def handle_query(query, fvecs, result_df, es, INDEX_NAME): #input query = 문제 id

    # fvecs = np.memmap(fvec_file, dtype='float32', mode='r').view('float32').reshape(-1, dim)

    SEARCH_SIZE = 4

    # embedding_start = time.time()

    query_vector = fvecs[result_df.loc[int(query),'index']]

    # embedding_time = time.time() - embedding_start # 시간 측정

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
    print("{} total hits.".format(response["hits"]["total"]["value"]))
    # print("embedding time: {:.2f} ms".format(embedding_time * 1000))
    print("search time: {:.2f} ms".format(search_time * 1000))
    similar_names = []
    similar_values = []
    for hit in response["hits"]["hits"]:
        print("id: {}, score: {}".format(hit["_source"]["Id"], hit["_score"]))
#         plot_images(hit["_source"]["Id"])
        similar_names.append("test" + hit["_source"]["Id"] + ".png")
        similar_values.append(hit["_score"])
    plotSimilarImages(similar_names, similar_values, SEARCH_SIZE)
