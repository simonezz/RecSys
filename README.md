# Recommender-System

Development of MATHFLAT's Algorithm for Recommendation of Similar Problems.
Extract the feature vector using Pre-trained MobileNet and measure cosine similarity.
Use Elasticsearch to get k questions with high cosine similarity.



## test1 (부분 테스트용)
  - Input : 문제 ID
  - Output : Input문제와 이미지상으로 유사한 문제 k개의 ID (k는 파라미터)


  ### Environment setup

  1. `conda create -n RecoSys python=3.7` : conda 환경 생성
  2. `source activate RecoSys` : conda 환경 활성화
  3. `pip install -r requirements.txt` : python packages 설치

  ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python test1/system/main.py
  ```
  
## test2

44만개정도의 데이터를 다 넣은 후 유사문제 검색, 문제 추가, 문제 업뎃 관련 코드

  1. Get.py : 문제 ID를 넣으면 유사 문제 ID들을 output으로 함.
  
 ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python test2/system/Get.py
  ```
  2. Index.py : 새로운 문제를 넣는 코드 (문제의 ID, unitCode, problemLevel, feature vector를 Elasticsearch에 추가)
  3. Update.py : 기존의 문제를 업데이트하는 코드 (문제의 ID, unitCode, problemLevel, feature vector를 Elasticsearch에 업데이트)
  (MySQL의 Datetime_update로 식별)
  

## server_test

1. get_server_client.py : 파이썬 소켓 서버를 이용하여 client가 문제 ID, 시작 순위, 마지막 순위를 보내면 서버에서 유사 문제 ID들을 돌려보내 줌.
2. put_server_client.py : 파이썬 소켓 서버를 이용하여 client가 datetime(ex. 20201005) 보내면 서버에서 datetime 이후에 DB에 add된 문제들을 Elasticsearch에 색인화.
3. twins_get_server_client.py : 파이썬 소켓 서버를 이용하여 client가 시중교재문제 ID, 시작 순위, 마지막 순위를 보내면 MySQL의 BookTwins 테이블에서 1:1 매칭되어 있는 문제은행 문제를 기준으로 Elasticsearch에서 유사문제를 찾아냄.
### Environment setup

  1. `conda create -n RecoSys_server python=3.7` : conda 환경 생성
  2. `source activate RecoSys_server` : conda 환경 활성화
  3. `pip install -r requirements.txt` : python packages 설치



### Run

  1. search_server_client.py
  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python server_test/get_server_client.py #server
  $ python server_test/get_server_client.py -c -id {문제 ID} -s {start} -e {end}#client  
  ```
ex) server_test/get_server_client.py -c -id 1 -s 0 -e 10 : returns problems data from rank 0 to 10 similar to id number 1.

  2. put_server_client.py

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python server_test/put_server_client.py #server
  $ python server_test/put_server_client.py -c -d {datetime} #client    
  ```
  3. twins_get_server_client.py
  
   ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python server_test/get_server_client.py #server
  $ python server_test/get_server_client.py -c -id {bookdata ID} -s {start} -e {end}#client  
  ```
  
## ElasticSearch_utils
  
  1. bulk_all_images_new.py : Code (very time consuming) putting all the problem data you are currently having (2020/09/23) into ElasticSearch (approximately 400,000) 
  (Id, unitCode,problemLevel,feature vector are present.)
  
  
  
## utils

  1. prepare_data.py : Extracts feature Vectors(using pre-trained MobileNet) of the problems which are same in terms of unitCode, problemLevel.

  2. bulk_feature_vectors.py : Index feature vectors in Elasticsearch.

  3. find_similar_problems.py : Returns similar vector k with input ID using cosine similarity of elasticsearch.
  
  4. general_utils.py : Collection of image-related functions (using one of these functions to parse ini files)
   
  5. hwp_parser.py : Extracts plain text or images from problem data (approximately 150,000) where hwp files exist among 15 curriculum data (BodyText, BinData, PrvText)

### Run

  5. hwp_parser.py

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python utils/hwp_parser.py --inputPath {input file path} --inputFile {input file name} --bodyText --w --outputPath{output text path} --outputFile {output text file name}
# When you want to extract bodyText from a hwp file (except from --w if you don't want to save result text)
  ```