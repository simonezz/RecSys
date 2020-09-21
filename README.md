# Recommender-System

MATHFLAT의 유사 문제 추천 알고리즘 개발
Pre-trained MobileNet을 이용하여 feature vector 추출 후 cosine 유사도 측정
Elasticsearch를 이용하여 cosine 유사도가 높은 문제가 k개 나오도록 함.

- Input : 문제 ID
- Output : Input문제와 이미지상으로 유사한 k개의 문제 ID 리스트 (k는 파라미터)


[utils 파일 설명]
1. prepare_data.py : Input으로 문제 ID를 받아 이 문제와 unitCode, problemLevel이 같은 문제들 가져온 후 MobileNet으로 Feature vector를 뽑아냄. 

2. bulk_feature_vectors.py : Elasticsearch에 feature vectors들을 색인화함. 

3. find_similar_problems.py : Elasticsearch의 cosine similarity를 이용하여 유사한 벡터 k개의 ID return.

## Environment setup

1. `conda create -n RecoSys python=3.7` : conda 환경 생성
2. `source activate RecoSys` : conda 환경 활성화
3. `pip install -r requirements.txt` : python packages 설치

## Run

```
$ conda activate ${CONDA_VIRTUAL_ENV}
$ python system/main.py
```
