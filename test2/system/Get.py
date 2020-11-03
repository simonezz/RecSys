# 데이터 이미 elasticsearch에 다 들어있다고 가정.
# 아이디 입력 시 similar 문제 상위 10개 보여주는 것으로 함.
import sys

from elasticsearch import Elasticsearch

sys.path.insert(0, '../../utils')
import general_utils as g_utils
import time

class RecommenderSystem:

    def __init__(self):

        self.ini_file = INI_FILE
        ini = g_utils.get_ini_parameters(self.ini_file)


        # Set parameters
        self.es = ini['ElasticSearch']['host'] # Elasticsearch Host
        self.index_name = ini['ElasticSearch']['INDEX_NAME']
        self.search_size = ini['ElasticSearch']['SEARCH_SIZE']# Similar problems 갯수

    def run(self):

        ID = int(input("Enter ID: "))

        es = Elasticsearch(self.es)

        SEARCH_SIZE = int(self.search_size)

        search_info_time = time.time()
        # 해당 아이디의 unitCode, problemLevel 찾기
        res = es.search(
            index=self.index_name,
            body={
                "query": {"match": {"_id": ID}}
            }
        )
        # print(res)
        if len(res['hits']['hits'])==0: #해당 ID가 Elasticsearch에 없다면,
            raise Exception("해당 ID가 Elasticsearch에 없습니다!")
        for s in res['hits']['hits']:
            fvec = s['_source']['fvec']
            unitCode = s['_source']['unitCode']
            problemLevel = s['_source']['problemLevel']
        print(f"문제 정보를 찾는데 걸리는 시간 : {(time.time()-search_info_time)} ms입니다.")

        # 위에서 구한 unitCode, problemLevel의 문제들 중 코사인 유사도 구하기

        script_query = {
            "script_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"unitCode": unitCode}},
                            {"match": {"problemLevel": problemLevel}}]}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'fvec') + 1.0",
                    "params": {"query_vector": fvec}
                }
            }
        }

        search_start = time.time()
        response = es.search(
            index=self.index_name,
            body={
                "size": SEARCH_SIZE,  # 유사한 벡터 몇 개 찾을건지
                "query": script_query,
                "_source": {"includes": ["_id", 'unitCode', 'problemLevel']}  # 일치하는 아이디
            }
        )

        print(f"유사 문제를 찾는데 걸리는 시간은 {(time.time() - search_start) * 1000} ms 입니다.")

        ID_list = []
        for s in response['hits']['hits']:

            print("ID: ", s['_id'])
            print("unitCode: ", s['_source']['unitCode'])
            print("problemLevel: ", s['_source']['problemLevel'])
            print("score: ", s['_score'])
            print('---------------------')
            if s['_score'] < 2:
                try:
                    if s['_id']==ID_list[-1]: #중복
                        pass
                    else:
                        ID_list.append(s['_id'])
                except:
                    ID_list.append(s['_id'])

        return ID_list

INI_FILE = 'Get.ini'

def main():

    reco_system = RecommenderSystem()

    print("similar ID List: ", reco_system.run())


if __name__ == "__main__":

    main()


