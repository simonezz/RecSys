# Recommender-System

MATHFLAT의 유사 문제 추천 알고리즘 개발
Pre-trained MobileNet을 이용하여 feature vector 추출 후 cosine 유사도 측정
Elasticsearch를 이용하여 Cosine 유사도가 높은 문제가 k개 나오도록 함.

  [utils]
  1. prepare_data.py : Input으로 문제 ID를 받아 이 문제와 unitCode, problemLevel이 같은 문제들 가져온 후 MobileNet으로 Feature vector를 뽑아냄. 

  2. bulk_feature_vectors.py : Elasticsearch에 feature vectors들을 색인화함. 

  3. find_similar_problems.py : Elasticsearch의 cosine similarity를 이용하여 유사한 벡터 k개의 ID return.
  
  4. general_utils.py : 이미지 관련 함수들 모음 (여기서 ini파일 파싱하는 함수 사용)
  
  [ElasticSearch_utils]
  
  1. bulk_all_images_new.py : 현재(2020/09/23)가지고 있는 문제(약 40만개)를 다 ElasticSearch에 넣는 코드(시간 소모 매우 큼)

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

  - Input : 문제 ID
  - Output : Input문제와 이미지상으로 유사한 문제 k개의 ID (k는 파라미터)
