# Recommender-System

MATHFLAT의 유사 문제 추천 알고리즘 개발
Pre-trained MobileNet을 이용하여 feature vector 추출 후 cosine 유사도 측정
Elasticsearch를 이용하여 Cosine 유사도가 높은 문제가 k개 나오도록 함.

  [utils]
  1. prepare_data.py : Input으로 문제 ID를 받아 이 문제와 unitCode, problemLevel이 같은 문제들 가져온 후 MobileNet으로 Feature vector를 뽑아냄. 

  2. bulk_feature_vectors.py : Elasticsearch에 feature vectors들을 색인화함. 

  3. find_similar_problems.py : Elasticsearch의 cosine similarity를 이용하여 유사한 벡터 k개의 ID return.
  
  4. general_utils.py : 이미지 관련 함수들 모음 (이 중 ini 파일 파싱하는 함수 사용)
  
  [ElasticSearch_utils]
  
  1. bulk_all_images_new.py : 현재(2020/09/23)가지고 있는 문제(약 40만개)를 다 ElasticSearch에 넣는 코드(시간 소모 매우 큼) -> 447879개의 데이터 있음
  (Id, unitCode, problemLevel, feature vector가 있음.)

## Test1 (부분 테스트용)
  - Input : 문제 ID
  - Output : Input문제와 이미지상으로 유사한 문제 k개의 ID (k는 파라미터)


  ### Environment setup

  1. `conda create -n RecoSys python=3.7` : conda 환경 생성
  2. `source activate RecoSys` : conda 환경 활성화
  3. `pip install -r requirements.txt` : python packages 설치

  ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python Test1/system/main.py
  ```
  
## Test2

44만개정도의 데이터를 다 넣은 후 유사문제 검색, 문제 추가, 문제 업뎃 관련 코드

  1. Get.py : 문제 ID를 넣으면 유사 문제 ID들을 output으로 함.
  
 ### Run

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python Test2/system/Get.py
  ```
  2. Index.py : 새로운 문제를 넣는 코드 (문제의 ID, unitCode, problemLevel, feature vector를 Elasticsearch에 추가)
  3. Update.py : 기존의 문제를 업데이트하는 코드 (문제의 ID, unitCode, problemLevel, feature vector를 Elasticsearch에 업데이트)
  (MySQL의 Datetime_update로 식별)
  

## Server_Test

1. search_server_client.py : 파이썬 소켓 서버를 이용하여 client가 문제 ID를 보내면 서버에서 유사 문제 ID들을 돌려보내 줌.
2. put_server_client.py : 파이썬 소켓 서버를 이용하여 client가 datetime(ex. 20201005) 보내면 서버에서 datetime 이후에 DB에 add된 문제들을 Elasticsearch에 색인화.

### Environment setup

  1. `conda create -n RecoSys_server python=3.7` : conda 환경 생성
  2. `source activate RecoSys_server` : conda 환경 활성화
  3. `pip install -r requirements.txt` : python packages 설치



### Run

  1. search_server_client.py
  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python Server_Test/search_server_client.py #server
  $ python Server_Test/search_server_client.py -c -id {문제 ID} #client    
  ```

  2. put_server_client.py

  ```
  $ conda activate ${CONDA_VIRTUAL_ENV}
  $ python Server_Test/put_server_client.py #server
  $ python Server_Test/put_server_client.py -c -d {datetime} #client    
  ```
   