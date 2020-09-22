# Put feature vectors of all the images into ElasticSearch
class RecommenderSystem:

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

        # Connect to MySQL
        self.user = ini['MySQL']['user']
        self.passwd = ini['MySQL']['passwd']
        self.host = ini['MySQL']['host']
        self.db = ini['MySQL']['db']
        self.charset = ini['MySQL']['charset']


        self.prob_db = pymysql.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset)


    def run(self):

        ID = input("Enter ID: ")
        df = get_similar_df(ID, self.prob_db)

        fvecs = extract_feature(df, int(self.batch_size), eval(self.input_shape), self.input_dir)  # save feature vectors to fvecs

        return fvecs, df, ID

INI_FILE = 'main.ini'

def main():
    reco_system = RecommenderSystem()
    f_vectors, cand_df, ID = reco_system.run()

    es = Elasticsearch(hosts=['localhost:9200'])
    data_bulk(es, cand_df, '../../utils/index.json', 'test', f_vectors)
    handle_query(ID, f_vectors, cand_df, es, 'test')

if __name__ == "__main__":

    main()


