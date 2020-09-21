from elasticsearch import Elasticsearch
from find_similar_problems import *
from prepare_data import *
from bulk_feature_vectors import *
import general_utils as g_utils

class SimilarSearch:

    """
    Initialization
    """

    def __init__(self):

        self.ini_file = INI_FILE
        ini = g_utils.get_ini_parameters(self.ini_file)

        # Set parameters
        self.dim = ini['PARAMS']['dim']
        self.batch_size = ini['PARAMS']['batch_size']
        self.input_shape = ini['PARAMS']['input_shape']
        self.input_dir = ini['PARAMS']['input_dir']

        # Set ElasticSearch
        self.INDEX_NAME = ini['ElasticSearch']['INDEX_NAME']
        self.INDEX_FILE = ini['ElasticSearch']['INDEX_FILE']

        # Connect to MySQL
        self.user = ini['MySQL']['user']
        self.passwd = ini['MySQL']['passwd']
        self.host = ini['MySQL']['host']
        self.db = ini['MySQL']['db']
        self.charset = ini['MySQL']['charset']


        self.prob_db = pymysql.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset)

        self.es_host = ini['ElasticSearch']['ESHOST']

    def run(self):
        es = Elasticsearch(hosts=[self.es_host])
        ID = input("Enter ID: ")
        df = get_similar_df(ID, self.prob_db)

        fvecs = extract_feature(df, int(self.batch_size), eval(self.input_shape), self.input_dir)  # save feature vectors to fvecs

        data_bulk(es, df, self.INDEX_FILE, self.INDEX_NAME, fvecs)

        handle_query(ID, fvecs, df, es, self.INDEX_NAME)

INI_FILE = './main.ini'

if __name__ == "__main__":

    similarsearch = SimilarSearch()
    similarsearch.run()
