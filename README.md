# Recommender-System

Development of MATHFLAT's Algorithm for Recommendation of Similar Problems.
Extract the feature vector using a pre-trained MobileNetV2 and measure cosine similarity.
Use Elasticsearch to get k questions with high cosine similarity.



## test1 (부분 테스트용)

1. main.py
  - Input : problem data ID
  - Output : k similar problem ID list for Input from image point of view (k:parameter)


  ### Environment setup

  1. `conda create -n RecoSys python=3.7` : create a conda environment 
  2. `source activate RecoSys` : activate the conda environment
  3. `pip install -r requirements.txt` : install python packages 

  ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python test1/system/main.py
  ```
  
## test2

Algorithms related to searching for similar problems data, adding problems data, and updating problems data after bulking 440,000 data


  1. Get.py : same as test1/main.py
  
 ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python test2/system/Get.py
  ```


  2. Index.py : Code for indexing new problems (add problem ID, unitCode, problemLevel, feature vector to Elasticsearch) 
  3. Update.py : Code for updating existing data ( ID, unitCode,problemLevel,feature vector updated to Elasticsearch)
(Identified by Datetime_update in MySQL) -> 불가능 판단..보류중
  

## server_test

1. get_server_client.py : Using Python Socket Server, when client sends problem ID, start rank, and last rank -> server sends similar problem ID back.
2. put_server_client.py : When clients send datetime (ex. 20201005) using Python socket server -> the server indexes the problems added to the DB after the datetime into Elasticsearch.
3. twins_get_server_client.py : When clients send their book data ID(시중문제), start rank, and last rank using Python Socket Server, -> server find similar problems in Elasticsearch based on 1:1 matching problem(문제은행) in MySQL's BookTwins table.
### Environment setup

  1. `conda create -n RecoSys_server python=3.7` : create a conda environment 
  2. `source activate RecoSys_server` : activate the conda environment
  3. `pip install -r requirements.txt` : install python packages



### Run

  1. search_server_client.py
  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python server_test/get_server_client.py #server
  $ python server_test/get_server_client.py -c -id {problem data ID} -s {start} -e {end}#client  
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

  6. hwp_split_pagewise.py : 페이지별로 단원이 나눠져 있기 때문에 페이지별로 한글 파일을 쪼개서 파싱한다.
  
  7. konlpy_utils.py : konlpy 관련 methods 저장.
  
  8. komoran_dict.tsv : konlpy중 komoran을 커스터마이즈하기 위한 사용자 사전.
### Run

  5. hwp_parser.py

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python utils/hwp_parser.py --inputPath {input file path} --inputFile {input file name} --bodyText --w --outputPath{output text path} --outputFile {output text file name}
# When you want to extract bodyText from a hwp file (except from --w if you don't want to save result text)
  ```