import time

import general_utils as g_utils
import pandas as pd
import pymysql
from elasticsearch import Elasticsearch


class Twins_get_id:

    def __init__(self):

        self.ini_file = INI_FILE
        ini = g_utils.get_ini_parameters(self.ini_file)
        # Set parameters
        self.es = ini['ElasticSearch']['host']  # Elasticsearch Host
        self.index_name = ini['ElasticSearch']['INDEX_NAME']
        self.search_size = ini['ElasticSearch']['SEARCH_SIZE']  # Similar problems 갯수 100으로 설정되어있음

        # Connect to MySQL
        self.user = ini['MySQL']['user']
        self.passwd = ini['MySQL']['passwd']
        self.host = ini['MySQL']['host']
        self.db = ini['MySQL']['db']
        self.charset = ini['MySQL']['charset']

        self.prob_db = pymysql.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db,
                                       charset=self.charset)

    def find_id(self, book_id):

        curs = self.prob_db.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT ID, bookCode, bookDataID, twinsProblemID FROM iclass.BookTwins"
        curs.execute(sql)
        twins_df = pd.DataFrame(curs.fetchall())
        id = twins_df.loc[twins_df['bookDataID'] == book_id, 'twinsProblemID']

        return id

    def run(self, ID):

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

        if len(res['hits']['hits']) == 0:  # 해당 ID가 Elasticsearch에 없다면,
            raise Exception("해당 ID가 Elasticsearch에 없습니다!")
        for s in res['hits']['hits']:
            fvec = s['_source']['fvec']
            unitCode = s['_source']['unitCode']
            problemLevel = s['_source']['problemLevel']
            print(f"문제 정보를 찾는데 걸리는 시간 : {(time.time() - search_info_time)} ms입니다.")

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

            if s['_score'] < 2:
                try:
                    if s['_id'] == ID_list[-1]:  # 중복
                        pass
                    else:
                        ID_list.append(s['_id'])
                except:
                    ID_list.append(s['_id'])

        return ID_list


INI_FILE = 'twins_get_server.ini'


def find_similar_pb(book_id):
    reco_system = Twins_get_id()
    prob_id = int(reco_system.find_id(book_id))
    # print(prob_id)

    return prob_id, reco_system.run(prob_id)
